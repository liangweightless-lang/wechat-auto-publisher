// SQLite 历史智库文库自闭环组件 (Self-contained History View Component)
import { state } from '../../store/state.js';
import { historyApi } from '../../api/historyApi.js';
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';
import { BottomSheet } from '../../components/BottomSheet.js';

let historyDrawer = null;

export function initHistoryDrawer() {
    if (historyDrawer) return historyDrawer;

    historyDrawer = new BottomSheet({
        id: 'historySheet',
        title: 'SQLite 历史智库文库',
        subtitle: '已沉淀的历史推文与全矩阵资产（轻点任意篇章即可一键恢复调阅）',
        icon: 'database',
        maxHeight: '85vh',
        renderBody: () => `
            <div id="historyListContainer" style="display: flex; flex-direction: column; gap: 10px;">
                <div class="sheet-loading-state">
                    <i data-lucide="loader-2" class="spin-icon" style="width: 20px; height: 20px;"></i>
                    <span>正在读取 SQLite 历史文库...</span>
                </div>
            </div>
        `,
        onOpen: loadHistoryArticles
    });

    return historyDrawer;
}

export function openHistoryDrawer() {
    const drawer = initHistoryDrawer();
    drawer.open();
}

export function closeHistoryDrawer() {
    if (historyDrawer) historyDrawer.close();
}

export async function loadHistoryArticles() {
    const container = document.getElementById('historyListContainer');
    if (!container) return;
    container.innerHTML = `
        <div class="sheet-loading-state">
            <i data-lucide="loader-2" class="spin-icon" style="width: 20px; height: 20px;"></i>
            <span>正在读取 SQLite 历史推文库...</span>
        </div>
    `;
    refreshIcons();

    try {
        const data = await historyApi.getHistory(30);
        if (data.code === 200 && data.articles && data.articles.length > 0) {
            renderHistoryCards(data.articles);
        } else {
            container.innerHTML = `
                <div class="sheet-loading-state">
                    <i data-lucide="archive" style="width: 28px; height: 28px; color: var(--text-light);"></i>
                    <span>文库暂无历史记录，去生成第一篇吧</span>
                </div>
            `;
            refreshIcons();
        }
    } catch (e) {
        container.innerHTML = `<div class="sheet-loading-state" style="color: #ef4444;">调阅失败: ${e.message}</div>`;
    }
}

export function renderHistoryCards(articles) {
    const container = document.getElementById('historyListContainer');
    if (!container) return;

    let html = '';
    articles.forEach(art => {
        const isPublished = art.publish_status === 'published';
        const statusBadge = isPublished
            ? '<span style="color: #16a34a; font-weight: 600;">已推草稿箱</span>'
            : '<span style="color: #ca8a04; font-weight: 600;">草稿存档</span>';

        let sourceNewsList = [];
        try { sourceNewsList = JSON.parse(art.source_news_json || '[]'); } catch(e) {}
        const hasSource = sourceNewsList.length > 0;
        const sourceTag = hasSource
            ? `<span class="history-source-tag" onclick="window.app.showSourceNewsModal(event, ${art.id}, '${encodeURIComponent(JSON.stringify(sourceNewsList))}')">
                <i data-lucide="newspaper" style="width: 10px; height: 10px;"></i>
                来源 ${sourceNewsList.length} 篇报道
               </span>`
            : '';

        html += `
        <div class="history-card" onclick="window.app.loadHistoryArticleDetail(${art.id})">
            <div class="history-card-header">
                <span class="history-card-tag">${art.category || '深度研判'}</span>
                <span class="history-card-time">${art.created_at ? art.created_at.substring(0,16) : ''}</span>
            </div>
            <div class="history-card-title">${art.title}</div>
            <div class="history-card-status">
                <i data-lucide="${isPublished ? 'check-circle' : 'file-edit'}" style="width: 12px; height: 12px; color: ${isPublished ? '#16a34a' : '#ca8a04'};"></i>
                <span>${statusBadge}</span>
                <span>·</span>
                <span>主题: ${art.theme || 'think_tank'}</span>
                ${hasSource ? '<span>·</span>' + sourceTag : ''}
            </div>
        </div>
        `;
    });
    container.innerHTML = html;
    refreshIcons();
}

export async function loadHistoryArticleDetail(id) {
    try {
        const data = await historyApi.getArticleById(id);
        if (data.code === 200 && data.article) {
            const art = data.article;
            state.currentGeneratedData = art;
            state.currentArticleId = art.id;

            const titleEl = document.getElementById('previewMockTitle');
            if (titleEl) titleEl.innerText = art.title;

            const bodyEl = document.getElementById('mobilePreviewContent');
            if (bodyEl) bodyEl.innerHTML = art.wechat_html || art.html_content;

            const dyEl = document.getElementById('douyinScriptText');
            if (dyEl) dyEl.value = art.douyin_script || '暂无矩阵脚本';

            const xhsEl = document.getElementById('xiaohongshuNoteText');
            if (xhsEl) xhsEl.value = art.xiaohongshu_note || '暂无小红书图文笔记';

            closeHistoryDrawer();
            if (window.app && window.app.switchMainTab) {
                window.app.switchMainTab('matrix');
            }
            showToast('已调出历史研报全文！', 'success');
        } else {
            showToast(data?.message || '调阅失败: 未找到指定文章', 'warning');
        }
    } catch (e) {
        console.error('调阅详情失败:', e);
        showToast('调阅详情异常: ' + (e.message || e), 'error');
    }
}

export function showSourceNewsModal(event, artId, encodedList) {
    if (event) event.stopPropagation();
    let list = [];
    try {
        list = JSON.parse(decodeURIComponent(encodedList));
    } catch (e) {
        list = [];
    }

    let modal = document.getElementById('sourceNewsModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'sourceNewsModal';
        modal.className = 'source-modal-mask';
        modal.innerHTML = `
        <div class="source-modal-dialog">
            <div class="source-modal-header">
                <div class="source-modal-title">
                    <i data-lucide="file-search" style="width: 15px; height: 15px; color: var(--primary);"></i>
                    <span>历史智库研报 · 事实信源追溯</span>
                </div>
                <button class="source-modal-close" onclick="document.getElementById('sourceNewsModal').classList.remove('active')">
                    <i data-lucide="x" style="width: 16px; height: 16px;"></i>
                </button>
            </div>
            <div class="source-modal-body" id="sourceNewsModalBody"></div>
        </div>
        `;
        document.body.appendChild(modal);
    }

    const bodyEl = document.getElementById('sourceNewsModalBody');
    if (bodyEl) {
        if (list.length === 0) {
            bodyEl.innerHTML = `<div style="text-align: center; color: var(--text-light); padding: 20px;">未关联原始报道信息</div>`;
        } else {
            let html = `<div style="font-size: 11.5px; color: var(--text-light); margin-bottom: 12px;">以下为本篇研报当初选题时绑定的真实公开信源：</div>`;
            list.forEach((item, idx) => {
                const isOfficial = !!item.is_official;
                html += `
                <div class="source-item-card">
                    <div class="source-item-top">
                        <span class="source-badge ${isOfficial ? 'official' : ''}">
                            ${isOfficial ? '<i data-lucide="shield-check" style="width: 10px; height: 10px;"></i>官方权威' : '<i data-lucide="radio" style="width: 10px; height: 10px;"></i>一手报道'}
                        </span>
                        <span class="source-name-pill">${item.source || '公开战报'}</span>
                        <span class="source-time-pill">${item.pub_time || ''}</span>
                    </div>
                    <div class="source-item-title">${item.title}</div>
                    ${item.url ? `
                    <div class="source-item-link">
                        <a href="${item.url}" target="_blank" style="color: var(--primary); text-decoration: none; font-size: 11px; display: inline-flex; align-items: center; gap: 3px;">
                            <i data-lucide="external-link" style="width: 11px; height: 11px;"></i>
                            <span>查看原始战报出处</span>
                        </a>
                    </div>` : ''}
                </div>
                `;
            });
            bodyEl.innerHTML = html;
        }
    }

    modal.classList.add('active');
    refreshIcons();
}
