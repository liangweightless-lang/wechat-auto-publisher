import { state, setSelectedArticle, removeSelectedArticle } from '../../store/state.js';
import { refreshIcons } from '../../utils/dom.js';

export function toggleSelectNews(clusterId, itemIdx, event) {
    if (event) event.stopPropagation();
    const cluster = state.currentClustersData.find(c => c.cluster_id === clusterId);
    if (!cluster || !cluster.items || !cluster.items[itemIdx]) return;

    const item = cluster.items[itemIdx];
    const key = `${clusterId}_${itemIdx}`;

    if (state.selectedArticlesMap.has(key)) {
        removeSelectedArticle(key);
    } else {
        setSelectedArticle(key, item);
    }

    updateSelectedUI();
}

export function selectAllInCluster(clusterId, event) {
    if (event) event.stopPropagation();
    const cluster = state.currentClustersData.find(c => c.cluster_id === clusterId);
    if (!cluster || !cluster.items) return;

    let allChecked = true;
    cluster.items.forEach((_, idx) => {
        const key = `${clusterId}_${idx}`;
        if (!state.selectedArticlesMap.has(key)) allChecked = false;
    });

    cluster.items.forEach((item, idx) => {
        const key = `${clusterId}_${idx}`;
        if (allChecked) {
            removeSelectedArticle(key);
        } else {
            setSelectedArticle(key, item);
        }
    });

    updateSelectedUI();
}

export function updateSelectedUI() {
    // 1. 同步所有子条目复选框样式
    document.querySelectorAll('.sub-news-item').forEach(el => {
        const key = el.id.replace('subItem_', '');
        const isChecked = state.selectedArticlesMap.has(key);
        el.classList.toggle('checked', isChecked);
        const box = el.querySelector('.sub-checkbox');
        if (box) {
            box.innerHTML = isChecked ? '<i data-lucide="check" style="width: 12px; height: 12px;"></i>' : '';
        }
    });

    // 2. 底部多选吸底工具条显示与计数
    const dock = document.getElementById('multiSelectDock');
    const badge = document.getElementById('selectedCountBadge');
    const count = state.selectedArticlesMap.size;

    if (badge) badge.innerText = count;
    if (dock) {
        dock.classList.toggle('active', count > 0);
    }

    // 3. 实时填入输入框
    const input = document.getElementById('mobileTopicInput');
    if (input) {
        if (count > 0) {
            const titles = Array.from(state.selectedArticlesMap.values()).map(a => a.title);
            input.value = `【多源情报交叉研判】已选定 ${count} 篇报道：\n` + titles.map((t, i) => `${i+1}. ${t}`).join('\n');
            input.style.borderColor = 'var(--primary)';
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 180) + 'px';
        } else {
            input.value = '';
            input.style.height = 'auto';
            input.style.borderColor = 'var(--border)';
        }
    }

    refreshIcons();
}

export function selectTopic(idx) {
    if (!state.currentClustersData || !state.currentClustersData[idx]) return;
    const cluster = state.currentClustersData[idx];
    const input = document.getElementById('mobileTopicInput');
    if (input) {
        input.value = cluster.main_title;
        input.style.borderColor = 'var(--primary)';
        state.selectedArticlesMap.clear();
        if (cluster.items && cluster.items.length > 0) {
            setSelectedArticle(`${cluster.cluster_id}_0`, cluster.items[0]);
            updateSelectedUI();
        }
    }
}

/**
 * 弹出已选多源情报合并清单详情模态框
 */
export function showSelectedArticlesModal() {
    const articles = Array.from(state.selectedArticlesMap.values());
    if (articles.length === 0) {
        showToast('当前尚未勾选任何报道', 'info');
        return;
    }

    let modal = document.getElementById('selectedArticlesModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'selectedArticlesModal';
        modal.className = 'source-modal-mask';
        modal.innerHTML = `
        <div class="source-modal-dialog" style="max-height: 85vh; display: flex; flex-direction: column;">
            <div class="source-modal-header" style="padding: 14px 18px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
                <div class="source-modal-title" style="display: flex; align-items: center; gap: 6px; font-weight: 700; font-size: 14px; color: var(--text-main);">
                    <i data-lucide="layers" style="width: 16px; height: 16px; color: var(--primary);"></i>
                    <span>已选多源合并情报池 (<span id="modalSelectedCount">0</span> 篇)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <button type="button" onclick="window.app.clearAllSelectedArticles()" style="padding: 4px 8px; border-radius: 6px; background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); font-size: 11px; cursor: pointer;">
                        清空全部
                    </button>
                    <button class="source-modal-close" onclick="window.app.closeSelectedArticlesModal()" style="background: transparent; border: none; cursor: pointer; color: var(--text-muted);">
                        <i data-lucide="x" style="width: 18px; height: 18px;"></i>
                    </button>
                </div>
            </div>
            <div class="source-modal-body" id="selectedArticlesModalBody" style="padding: 14px 16px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 10px;"></div>
            <div style="padding: 12px 18px; border-top: 1px solid var(--border); background: var(--bg-surface); display: flex; justify-content: space-between; align-items: center; gap: 10px;">
                <button type="button" onclick="window.app.closeSelectedArticlesModal()" style="flex: 1; height: 40px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-main); font-size: 13px; font-weight: 600; cursor: pointer;">
                    返回继续勾选
                </button>
                <button type="button" onclick="window.app.startMergedGenerateFromModal()" style="flex: 1.5; height: 40px; border-radius: 8px; border: none; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; font-size: 13.5px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);">
                    <i data-lucide="sparkles" style="width: 15px; height: 15px;"></i>
                    <span>确认合并并开始研判</span>
                </button>
            </div>
        </div>
        `;
        document.body.appendChild(modal);
    }

    renderSelectedModalBody();
    modal.classList.add('active');
    refreshIcons();
}

export function closeSelectedArticlesModal() {
    const modal = document.getElementById('selectedArticlesModal');
    if (modal) modal.classList.remove('active');
}

export function renderSelectedModalBody() {
    const bodyEl = document.getElementById('selectedArticlesModalBody');
    const countEl = document.getElementById('modalSelectedCount');
    const articlesMap = state.selectedArticlesMap;
    const count = articlesMap.size;

    if (countEl) countEl.innerText = count;
    if (!bodyEl) return;

    if (count === 0) {
        bodyEl.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
                <i data-lucide="inbox" style="width: 32px; height: 32px; margin-bottom: 8px; opacity: 0.5;"></i>
                <div style="font-size: 13px;">尚未勾选任何情报报道</div>
            </div>
        `;
        refreshIcons();
        return;
    }

    let html = '';
    let idx = 1;
    for (const [key, art] of articlesMap.entries()) {
        const isOfficial = !!art.is_official;
        html += `
        <div class="source-item-card" style="padding: 12px 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg-card); position: relative;">
            <div class="source-item-top" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    <span style="display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 50%; background: var(--primary); color: #fff; font-size: 10.5px; font-weight: 700;">
                        ${idx}
                    </span>
                    <span class="source-badge ${isOfficial ? 'official' : ''}" style="font-size: 10.5px; padding: 2px 6px; border-radius: 4px; background: rgba(37,99,235,0.1); color: var(--primary); font-weight: 600;">
                        ${isOfficial ? '官方权威' : '一手报道'}
                    </span>
                    <span style="font-size: 11.5px; font-weight: 600; color: var(--text-main);">${art.source || '公开战报'}</span>
                    <span style="font-size: 10.5px; color: var(--text-muted);">${art.pub_time || '实时'}</span>
                </div>
                <button type="button" onclick="window.app.removeSelectedArticleByKey('${key}')" style="padding: 3px 6px; border-radius: 4px; border: none; background: rgba(239, 68, 68, 0.08); color: #ef4444; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 3px;" title="从合并池移除">
                    <i data-lucide="trash-2" style="width: 12px; height: 12px;"></i>
                    <span>移除</span>
                </button>
            </div>
            <div class="source-item-title" style="font-size: 13.5px; font-weight: 700; color: var(--text-main); line-height: 1.4; margin-bottom: 6px;">
                ${art.title}
            </div>
            ${art.summary ? `
            <div style="font-size: 12px; color: var(--text-muted); line-height: 1.5; background: var(--bg-surface); padding: 8px 10px; border-radius: 6px; margin-bottom: 6px;">
                ${art.summary}
            </div>` : ''}
            ${art.url ? `
            <div style="text-align: right;">
                <a href="${art.url}" target="_blank" style="color: var(--primary); font-size: 11.5px; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 3px;">
                    <span>查看媒体原始出处</span>
                    <i data-lucide="external-link" style="width: 11px; height: 11px;"></i>
                </a>
            </div>` : ''}
        </div>
        `;
        idx++;
    }

    bodyEl.innerHTML = html;
    refreshIcons();
}

export function removeSelectedArticleByKey(key) {
    removeSelectedArticle(key);
    updateSelectedUI();
    renderSelectedModalBody();
    if (state.selectedArticlesMap.size === 0) {
        closeSelectedArticlesModal();
    }
}

export function clearAllSelectedArticles() {
    state.selectedArticlesMap.clear();
    updateSelectedUI();
    closeSelectedArticlesModal();
    showToast('已清空全部选定的情报源', 'info');
}

export function startMergedGenerateFromModal() {
    closeSelectedArticlesModal();
    if (window.app && window.app.triggerMultiSelectGenerate) {
        window.app.triggerMultiSelectGenerate();
    }
}
