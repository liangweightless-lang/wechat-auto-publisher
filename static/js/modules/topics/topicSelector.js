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

    // 2. 底部浮动选择条显示与计数
    const bar = document.getElementById('multiSelectFloatBar');
    const countBadge = document.getElementById('selectedCountBadge');
    const selectedList = Array.from(state.selectedArticlesMap.values());
    const count = selectedList.length;

    if (bar) {
        if (count > 0) {
            bar.classList.add('visible');
            if (countBadge) countBadge.textContent = `${count} 篇情报`;
        } else {
            bar.classList.remove('visible');
        }
    }

    // 3. 实时填入输入框
    const topicInput = document.getElementById('mobileTopicInput');
    if (topicInput && count > 0) {
        const titles = selectedList.map((it, i) => `${i + 1}. 【${it.source || '一手防务'}】${it.title}`).join('\n');
        topicInput.value = titles;
        topicInput.style.borderColor = 'var(--primary)';
    }

    refreshIcons();
}

export function selectTopic(idx) {
    // 兼容快捷单选卡片
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
