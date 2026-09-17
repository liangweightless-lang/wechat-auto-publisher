import { state } from '../../store/state.js';
import { topicsApi } from '../../api/topicsApi.js';
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';
import { toggleSelectNews, selectAllInCluster } from './topicSelector.js';

export function renderSkeletonLoading() {
    return `
    <div class="feed-top-loader">
        <div class="feed-loader-spinner"></div>
        <span>正在跨网聚合全网最新战略情报与官方通报...</span>
    </div>

    <div class="standard-skeleton-card">
        <div class="skeleton-row">
            <div class="skeleton-bar" style="width: 58px; height: 16px; border-radius: 10px;"></div>
            <div class="skeleton-bar" style="width: 48px; height: 14px; border-radius: 4px;"></div>
        </div>
        <div class="skeleton-bar" style="width: 78%; height: 16px; margin-top: 2px;"></div>
        <div class="skeleton-bar" style="width: 95%; height: 13px;"></div>
        <div class="skeleton-row" style="margin-top: 4px;">
            <div class="skeleton-bar" style="width: 90px; height: 12px;"></div>
            <div class="skeleton-bar" style="width: 40px; height: 14px; border-radius: 8px;"></div>
        </div>
    </div>

    <div class="standard-skeleton-card">
        <div class="skeleton-row">
            <div class="skeleton-bar" style="width: 50px; height: 16px; border-radius: 10px;"></div>
            <div class="skeleton-bar" style="width: 42px; height: 14px; border-radius: 4px;"></div>
        </div>
        <div class="skeleton-bar" style="width: 70%; height: 16px; margin-top: 2px;"></div>
        <div class="skeleton-bar" style="width: 88%; height: 13px;"></div>
        <div class="skeleton-row" style="margin-top: 4px;">
            <div class="skeleton-bar" style="width: 80px; height: 12px;"></div>
            <div class="skeleton-bar" style="width: 36px; height: 14px; border-radius: 8px;"></div>
        </div>
    </div>

    <div class="standard-skeleton-card">
        <div class="skeleton-row">
            <div class="skeleton-bar" style="width: 62px; height: 16px; border-radius: 10px;"></div>
            <div class="skeleton-bar" style="width: 45px; height: 14px; border-radius: 4px;"></div>
        </div>
        <div class="skeleton-bar" style="width: 65%; height: 16px; margin-top: 2px;"></div>
        <div class="skeleton-bar" style="width: 92%; height: 13px;"></div>
        <div class="skeleton-row" style="margin-top: 4px;">
            <div class="skeleton-bar" style="width: 70px; height: 12px;"></div>
            <div class="skeleton-bar" style="width: 38px; height: 14px; border-radius: 8px;"></div>
        </div>
    </div>
    `;
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

            if (data.dynamic_categories && data.dynamic_categories.length > 0) {
                state.dynamicCategories = data.dynamic_categories;
                renderDynamicCategories(data.dynamic_categories, cat);
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

export function formatDisplayTime(rawTime, idx = 0) {
    if (!rawTime || rawTime === '实时' || rawTime === '今日最新' || rawTime === '刚刚') {
        if (idx === 0) return '刚刚';
        if (idx === 1) return '8分钟前';
        if (idx === 2) return '16分钟前';
        if (idx === 3) return '28分钟前';
        if (idx <= 6) return `${idx * 12}分钟前`;
        return `${Math.min(6, Math.floor(idx / 3) + 1)}小时前`;
    }
    return rawTime;
}

export function renderClusters(clusters) {
    const listEl = document.getElementById('mobileHotList');
    if (!listEl) return;

    let html = '';
    clusters.forEach((cluster, cIdx) => {
        const isOpen = cIdx === 0;
        const sourcesText = (cluster.sources || []).map(s => s.replace(/[\uD83C-\uDBFF\uDC00-\uDFFF\u2600-\u27BF]/g, '').trim()).slice(0, 3).join(' · ');

        const CATEGORY_MAP = {
            'all': '综合焦点',
            'military_hot': '军事焦点',
            'weapons': '先进装备',
            'relations': '大国博弈',
            'regional_intel': '区域态势'
        };
        const hasOfficial = (cluster.items || []).some(it => it.is_official);
        const rawCat = cluster.category || 'military_hot';
        const displayCat = hasOfficial ? '官方权威' : (CATEGORY_MAP[rawCat] || '综合焦点');
        const isSingle = (cluster.topic_count || (cluster.items ? cluster.items.length : 1)) <= 1;
        const showSubPreview = !isSingle && cluster.main_title && cluster.main_title !== cluster.cluster_name;

        const badgeText = cluster.badge || (hasOfficial ? '官方' : '国际');
        const badgeClass = cluster.badge_class || (hasOfficial ? 'badge-domestic' : 'badge-intl');
        const hotScore = cluster.hot_score || (90 + (cIdx < 3 ? (8 - cIdx * 2) : 0));
        const displayTitle = cluster.cluster_name || cluster.main_title;
        const keywordsList = (cluster.keywords && cluster.keywords.length > 0) ? cluster.keywords : ['#战略研判', '#重点要闻'];

        html += `
        <div class="cluster-card ${isOpen ? 'open' : ''}" id="clusterCard_${cluster.cluster_id}">
            <div class="cluster-header" onclick="window.app.toggleCluster('${cluster.cluster_id}')">
                <!-- 1. 顶部主标题栏 (左侧分类方形色块徽章 + 主标题，对标截图) -->
                <div class="card-headline-row">
                    <span class="category-square-badge ${badgeClass}">${badgeText}</span>
                    <h3 class="cluster-heading">${displayTitle}</h3>
                </div>
                ${showSubPreview ? `<p class="cluster-sub-preview">${cluster.main_title}</p>` : ''}

                <!-- 2. 中间：发布时间(带时钟图标) + 篇数 + 右侧金黄色 "热 98" 评级 -->
                <div class="card-meta-bar">
                    <div class="card-time-text">
                        <i data-lucide="clock" class="time-clock-icon"></i>
                        <span class="time-text-val">${formatDisplayTime(cluster.latest_time, cIdx)}</span>
                        ${cluster.topic_count > 1 ? `<span class="card-layers-tag">· ${cluster.topic_count} 篇交叉印证</span>` : ''}
                    </div>
                    <div class="card-hot-rating">
                        <span class="hot-label">热</span>
                        <span class="hot-value">${hotScore}</span>
                        <i data-lucide="chevron-down" class="cluster-arrow-icon"></i>
                    </div>
                </div>



                <!-- 4. 底部多标签药丸栏 (#先进制造 #政策定调 #新质生产力，对标截图) -->
                <div class="cluster-keywords-row">
                    ${keywordsList.map(kw => `<span class="kw-tag">${kw}</span>`).join("")}
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
                        <span>检索更多关联报道与官方通报</span>
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
                        <span>${formatDisplayTime(pubTime, itemIdx)}</span>
                    </span>
                    ${(item.keywords && item.keywords.length > 0) ? `
                        <span class="sub-kw-group">
                            ${item.keywords.slice(0, 2).map(k => `<span class="sub-kw-tag">${k}</span>`).join("")}
                        </span>
                    ` : ""}
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
    btn.innerHTML = `<i data-lucide="loader-2" class="spin" style="width: 13px; height: 13px;"></i> <span>正在检索关联权威报道与通报...</span>`;
    btn.disabled = true;
    refreshIcons();

    try {
        const data = await topicsApi.expandOfficialSources(cluster.main_title, cluster.cluster_name);
        if (data && data.items && data.items.length > 0) {
            cluster.items = cluster.items.concat(data.items);
            cluster.topic_count = cluster.items.length;
            subList.innerHTML = renderSubNewsItems(cluster.cluster_id, cluster.items);
            btn.innerHTML = `<i data-lucide="check" style="width: 13px; height: 13px; color: #10b981;"></i> <span>已聚合 ${data.items.length} 篇关联权威报道与通报</span>`;
            showToast(`成功补充 ${data.items.length} 条关联权威报道与通报！`, 'success');
        } else {
            btn.innerHTML = `<i data-lucide="info" style="width: 13px; height: 13px;"></i> <span>暂无更多最新关联报道</span>`;
        }
    } catch (e) {
        btn.innerHTML = origText;
        showToast('扩展信源失败，请重试', 'error');
    } finally {
        refreshIcons();
        setTimeout(() => { if (btn) btn.disabled = false; }, 3000);
    }
}

export function renderDynamicCategories(categories, activeId = 'all') {
    const stripEl = document.getElementById('categoryScrollStrip');
    if (!stripEl || !Array.isArray(categories) || categories.length === 0) return;

    stripEl.innerHTML = categories.map(cat => `
        <button class="category-pill ${cat.id === activeId ? 'active' : ''}" 
                onclick="window.app.filterByDynamicCategory('${cat.id}', this)">
            ${cat.id === 'all' ? '<i data-lucide="radar" class="pill-icon"></i>' : ''}
            <span>${cat.name}</span>
            <span class="cat-pill-count">${cat.count}</span>
        </button>
    `).join('');
    refreshIcons();
}

export function filterByDynamicCategory(catId, btnEl) {
    state.currentCategory = catId;
    document.querySelectorAll('.category-pill').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    const allClusters = state.currentClustersData || [];
    if (catId === 'all') {
        renderClusters(allClusters);
    } else {
        const catNameMap = {
            'domestic': '国内',
            'tech': '科技',
            'military': '军事',
            'intl': '国际',
            'livelihood': '民生'
        };
        const targetBadge = catNameMap[catId] || '';
        const filtered = allClusters.filter(c => 
            c.category === catId || 
            c.badge === targetBadge || 
            c.badge === catId || 
            c.cluster_id === catId
        );
        renderClusters(filtered.length > 0 ? filtered : allClusters);
    }
}
