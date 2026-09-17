import { state } from '../../store/state.js';
import { topicsApi } from '../../api/topicsApi.js';
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';
import { toggleSelectNews, selectAllInCluster } from './topicSelector.js';

export function renderSkeletonLoading() {
    let skeletons = `
    <div class="feed-loading-banner" style="display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; font-size: 12.5px; color: var(--primary); background: rgba(37, 99, 235, 0.07); border: 1px dashed rgba(37, 99, 235, 0.25); border-radius: 8px; margin-bottom: 12px;">
        <i data-lucide="loader-2" class="spin" style="width: 15px; height: 15px;"></i>
        <span>正在跨网聚合联合国/塔斯社/外网官方战报并智能聚类排序...</span>
    </div>
    `;
    for (let i = 0; i < 4; i++) {
        skeletons += `
        <div class="feed-skeleton-card" style="margin-bottom: 10px; padding: 14px; background: var(--bg-card); border-radius: 10px; border: 1px solid var(--border);">
            <div class="skeleton-line shimmer" style="height: 16px; width: 65%; margin-bottom: 8px; border-radius: 4px; background: var(--bg-hover);"></div>
            <div class="skeleton-line shimmer" style="height: 13px; width: 90%; margin-bottom: 10px; border-radius: 4px; background: var(--bg-hover);"></div>
            <div class="skeleton-meta shimmer" style="height: 12px; width: 40%; border-radius: 4px; background: var(--bg-hover);"></div>
        </div>`;
    }
    return skeletons;
}

export async function fetchAndRenderTopics(cat = 'all', forceRefresh = false) {
    const listEl = document.getElementById('mobileHotList');
    const refreshBtn = document.getElementById('feedRefreshBtn');
    const refreshIcon = document.getElementById('feedRefreshIcon');

    // 触发按钮 Loading 动效
    if (refreshBtn) refreshBtn.disabled = true;
    if (refreshIcon) refreshIcon.classList.add('spin');

    // 若非强制刷新且本地有缓存，优先毫秒级加载缓存
    if (!forceRefresh && state.clientClustersCache.has(cat)) {
        const cached = state.clientClustersCache.get(cat);
        state.currentClustersData = cached;
        renderClusters(cached);
        if (refreshBtn) refreshBtn.disabled = false;
        if (refreshIcon) refreshIcon.classList.remove('spin');
        return;
    }

    if (listEl) {
        listEl.innerHTML = renderSkeletonLoading();
        refreshIcons();
    }

    try {
        const data = await topicsApi.fetchTopics(cat, true, forceRefresh);
        if (data && data.clusters && data.clusters.length > 0) {
            state.currentClustersData = data.clusters;
            state.clientClustersCache.set(cat, data.clusters);

            const syncTimeEl = document.getElementById('feedSyncTime');
            if (syncTimeEl) {
                const nowStr = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                syncTimeEl.innerHTML = `<i data-lucide="clock" style="width: 11px; height: 11px;"></i> <span>上次更新：${nowStr} · 自动同步</span>`;
            }

            renderClusters(data.clusters);
            if (forceRefresh) {
                showToast('已获取全网最新一手防务情报与官方通报！', 'success');
            }
        } else {
            if (listEl) {
                listEl.innerHTML = `
                    <div class="feed-empty-state">
                        <i data-lucide="inbox" style="width: 22px; height: 22px; color: var(--text-light);"></i>
                        <span>暂未检索到该分类情报，轻点右上角刷新重试</span>
                    </div>
                `;
            }
            refreshIcons();
        }
    } catch (e) {
        if (listEl) {
            listEl.innerHTML = `<div class="feed-empty-state" style="color: #ef4444;">拉取情报异常: ${e.message}</div>`;
        }
    } finally {
        if (refreshBtn) refreshBtn.disabled = false;
        if (refreshIcon) refreshIcon.classList.remove('spin');
        refreshIcons();
    }
}

export function renderClusters(clusters) {
    const listEl = document.getElementById('mobileHotList');
    if (!listEl) return;

    let html = '';
    clusters.forEach((cluster, cIdx) => {
        const isOpen = cIdx === 0;
        const sourcesText = (cluster.sources || []).map(s => s.replace(/[\uD83C-\uDBFF\uDC00-\uDFFF\u2600-\u27BF]/g, '').trim()).slice(0, 3).join(' · ');

        html += `
        <div class="cluster-card ${isOpen ? 'open' : ''}" id="clusterCard_${cluster.cluster_id}">
            <div class="cluster-header" onclick="window.app.toggleCluster('${cluster.cluster_id}')">
                <div class="cluster-title-col">
                    <div class="cluster-name-row">
                        <span class="cluster-tag">${cluster.category || '综合焦点'}</span>
                        <span class="cluster-name">${cluster.cluster_name}</span>
                    </div>
                    <div class="cluster-main-preview">${cluster.main_title}</div>
                </div>
                <div class="cluster-meta-right">
                    <span class="cluster-time-pill">
                        <i data-lucide="clock-3" style="width: 11px; height: 11px;"></i>
                        <span>${cluster.latest_time || '今日最新'}</span>
                    </span>
                    <span class="cluster-count-badge">
                        <i data-lucide="layers-2" style="width: 12px; height: 12px;"></i>
                        <span>${cluster.topic_count} 篇</span>
                    </span>
                    <i data-lucide="chevron-down" class="cluster-arrow-icon"></i>
                </div>
            </div>
            <div class="cluster-body" id="clusterBody_${cluster.cluster_id}">
                <div class="cluster-quick-actions">
                    <span>覆盖源: ${sourcesText}</span>
                    <button class="select-all-btn" onclick="window.app.selectAllInCluster('${cluster.cluster_id}', event)">
                        <i data-lucide="check-square" style="width: 12px; height: 12px;"></i>
                        <span>全选本专题</span>
                    </button>
                </div>
                <div class="sub-news-list" id="subList_${cluster.cluster_id}">
                    ${renderSubNewsItems(cluster.cluster_id, cluster.items)}
                </div>
                <div class="expand-sources-container">
                    <button class="expand-sources-btn" id="expandBtn_${cluster.cluster_id}" onclick="window.app.expandOfficialSources('${cluster.cluster_id}', event)">
                        <i data-lucide="shield" style="width: 13px; height: 13px;"></i>
                        <span>搜集本事件更多官方公告与外交部发言</span>
                    </button>
                </div>
            </div>
        </div>
        `;
    });

    listEl.innerHTML = html;
    refreshIcons();
}

export function renderSubNewsItems(clusterId, items) {
    let subHtml = '';
    items.forEach((item, itemIdx) => {
        const key = `${clusterId}_${itemIdx}`;
        const isChecked = state.selectedArticlesMap.has(key);
        const source = (item.source || '官方通报').replace(/[\uD83C-\uDBFF\uDC00-\uDFFF\u2600-\u27BF]/g, '').trim();
        const pubTime = item.pub_time || '刚刚';
        const url = item.url || '';
        const isOfficial = !!item.is_official;

        subHtml += `
        <div class="sub-news-item ${isChecked ? 'checked' : ''} ${isOfficial ? 'official-item' : ''}" id="subItem_${key}" onclick="window.app.toggleSelectNews('${clusterId}', ${itemIdx}, event)">
            <div class="sub-checkbox">
                ${isChecked ? '<i data-lucide="check" style="width: 12px; height: 12px;"></i>' : ''}
            </div>
            <div class="sub-news-body">
                <div class="sub-news-title">
                    ${isOfficial ? '<span class="official-badge-gold"><i data-lucide="shield-check" style="width: 10px; height: 10px;"></i>官方权威</span> ' : ''}
                    ${item.title}
                    ${item.title_original ? `<div class="sub-news-original-title" style="font-size: 11.5px; color: #94a3b8; margin-top: 3px; font-style: italic; line-height: 1.35;"><span style="color: #64748b; font-weight: 600; font-style: normal; background: rgba(148, 163, 184, 0.12); padding: 1px 4px; border-radius: 3px; margin-right: 4px;">英译汉</span>${item.title_original}</div>` : ''}
                </div>
                <div class="sub-news-meta">
                    <span class="meta-source-tag">${source}</span>
                    <span>·</span>
                    <span class="meta-time-tag">
                        <i data-lucide="clock" style="width: 10px; height: 10px;"></i>
                        <span>${pubTime}</span>
                    </span>
                    ${url ? `<span>·</span><a href="${url}" target="_blank" onclick="event.stopPropagation()" style="color: var(--primary); text-decoration: none; display: inline-flex; align-items: center; gap: 2px;"><i data-lucide="external-link" style="width: 10px; height: 10px;"></i>出处公告</a>` : ''}
                </div>
            </div>
        </div>
        `;
    });
    return subHtml;
}

export function toggleCluster(clusterId) {
    const card = document.getElementById(`clusterCard_${clusterId}`);
    if (card) {
        card.classList.toggle('open');
        refreshIcons();
    }
}

export async function expandOfficialSources(clusterId, event) {
    if (event) event.stopPropagation();
    const btn = document.getElementById(`expandBtn_${clusterId}`);
    const subList = document.getElementById(`subList_${clusterId}`);
    const cluster = state.currentClustersData.find(c => c.cluster_id === clusterId);

    if (!btn || !subList || !cluster) return;

    const origText = btn.innerHTML;
    btn.innerHTML = `<i data-lucide="loader-2" class="spin" style="width: 13px; height: 13px;"></i> <span>正在跨网搜集外交部答问与国防部公报...</span>`;
    btn.disabled = true;
    refreshIcons();

    try {
        const data = await topicsApi.expandOfficialSources(cluster.main_title, cluster.cluster_name);
        if (data && data.items && data.items.length > 0) {
            cluster.items = cluster.items.concat(data.items);
            cluster.topic_count = cluster.items.length;
            subList.innerHTML = renderSubNewsItems(cluster.cluster_id, cluster.items);
            btn.innerHTML = `<i data-lucide="check" style="width: 13px; height: 13px; color: #10b981;"></i> <span>已聚合 ${data.items.length} 篇权威官方立场公告</span>`;
            showToast(`成功补充 ${data.items.length} 条官方外交部/国防部权威报道！`, 'success');
        } else {
            btn.innerHTML = `<i data-lucide="info" style="width: 13px; height: 13px;"></i> <span>暂无更多最新官方答问</span>`;
        }
    } catch (e) {
        btn.innerHTML = origText;
        showToast('扩展信源失败，请重试', 'error');
    } finally {
        refreshIcons();
        setTimeout(() => { if (btn) btn.disabled = false; }, 3000);
    }
}
