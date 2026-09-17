// 前端企业级主入口 (Enterprise Main App Entry)
import { state } from './store/state.js';
import { refreshIcons } from './utils/dom.js';
import { showToast } from './utils/toast.js';
import { initTheme, toggleTheme, openBottomSheet, closeBottomSheet, closeAllSheets } from './modules/theme/themeManager.js';
import { fetchAndRenderTopics, toggleCluster, expandOfficialSources } from './modules/topics/topicCards.js';
import { toggleSelectNews, selectAllInCluster, selectTopic, updateSelectedUI } from './modules/topics/topicSelector.js';
import { triggerMobileGenerate, toggleThinking } from './modules/generator/streamHandler.js';
import { switchPlatform, copyActiveContent } from './modules/matrix/matrixView.js';
import { loadHistoryArticles, loadHistoryArticleDetail, showSourceNewsModal } from './modules/history/historyView.js';
import { loadStrategyData, sendStrategyTuneMessage, triggerAiRadarRefresh, resetStrategyToDefault } from './modules/strategy/strategyChat.js';
import { publishApi } from './api/publishApi.js';

// 页面 Tab 切换
export function switchMainTab(tabName) {
    const tabTopics = document.getElementById('tabNavTopics');
    const tabPreview = document.getElementById('tabNavPreview');
    const viewTopics = document.getElementById('viewTopics');
    const viewPreview = document.getElementById('viewPreview');
    const topBar = document.getElementById('previewTopBar');

    if (tabName === 'topics') {
        if (tabTopics) tabTopics.classList.add('active');
        if (tabPreview) tabPreview.classList.remove('active');
        if (viewTopics) viewTopics.classList.add('active');
        if (viewPreview) viewPreview.classList.remove('active');
        if (topBar) topBar.classList.remove('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (tabName === 'preview') {
        if (tabTopics) tabTopics.classList.remove('active');
        if (tabPreview) tabPreview.classList.add('active');
        if (viewTopics) viewTopics.classList.remove('active');
        if (viewPreview) viewPreview.classList.add('active');
        if (topBar) topBar.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    refreshIcons();
}

// 分类切换
export function selectCategory(cat, el) {
    state.currentCategory = cat;
    document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
    if (el) el.classList.add('active');
    fetchAndRenderTopics(cat, false);
}

// 刷新情报
export function refreshCurrentFeed() {
    fetchAndRenderTopics(state.currentCategory, true);
}

// 清空选题输入框
export function clearTopicInput() {
    const input = document.getElementById('mobileTopicInput');
    if (input) {
        input.value = '';
        input.style.borderColor = 'var(--border)';
    }
    state.selectedArticlesMap.clear();
    updateSelectedUI();
    showToast('已清空选题内容与选中的情报', 'info');
}

// 快速换肤与重排
export async function switchThemeQuick(themeKey, btnEl) {
    document.querySelectorAll('.theme-quick-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    const previewBody = document.getElementById('previewHtmlBody');
    if (!previewBody || !previewBody.innerHTML.trim()) {
        showToast('请先生成文章后再切换视觉排版', 'warning');
        return;
    }

    try {
        const res = await publishApi.formatPreview(themeKey);
        if (res && res.code === 200 && res.html) {
            previewBody.innerHTML = res.html;
            showToast(`🎨 已切换为【${themeKey}】排版风格`, 'success');
        }
    } catch (e) {
        showToast('换肤失败', 'error');
    }
}

// 微信公众号草稿箱真实推送
export async function triggerMobilePublish() {
    if (state.currentActivePlatform !== 'wechat') {
        copyActiveContent();
        return;
    }

    const pubBtn = document.getElementById('mobilePublishBtn');
    const pubText = document.getElementById('mobilePubText');
    const origText = pubText ? pubText.innerText : '';

    if (pubBtn) pubBtn.disabled = true;
    if (pubText) pubText.innerText = '正在推送到微信公众平台草稿箱...';

    try {
        const res = await publishApi.publishToWechat();
        if (res.code === 200) {
            showToast(`🚀 成功推送到微信公众平台草稿箱！Media ID: ${res.media_id ? res.media_id.substring(0, 10) : '已生成'}`, 'success');
        } else {
            showToast(`推送失败: ${res.message || '请检查微信凭据配置'}`, 'error');
        }
    } catch (e) {
        showToast(`推送异常: ${e.message}`, 'error');
    } finally {
        if (pubBtn) pubBtn.disabled = false;
        if (pubText) pubText.innerText = origText;
        refreshIcons();
    }
}

// 全局命名空间挂载 (兼顾 HTML 原生 onclick 属性与模块化)
window.app = {
    switchMainTab,
    selectCategory,
    refreshCurrentFeed,
    toggleCluster,
    toggleSelectNews,
    selectAllInCluster,
    selectTopic,
    clearTopicInput,
    expandOfficialSources,
    triggerMobileGenerate,
    toggleThinking,
    switchPlatform,
    copyActiveContent,
    triggerMobilePublish,
    switchThemeQuick,
    openBottomSheet,
    closeBottomSheet,
    closeAllSheets,
    loadHistoryArticles,
    loadHistoryArticleDetail,
    showSourceNewsModal,
    sendStrategyTuneMessage,
    triggerAiRadarRefresh,
    resetStrategyToDefault,
    toggleTheme,
    refreshIcons
};

// 页面加载生命周期
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    refreshIcons();
    fetchAndRenderTopics('all', false);
    loadStrategyData();

    // 绑定全局遮罩点击关闭
    const mask = document.getElementById('sheetMask');
    if (mask) {
        mask.addEventListener('click', closeAllSheets);
    }

    // 绑定策略输入框回车发送
    const strategyInput = document.getElementById('strategyChatInput');
    if (strategyInput) {
        strategyInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendStrategyTuneMessage();
            }
        });
    }
});

// 全局暴露所有函数，确保原生 HTML onclick 完美调用
Object.assign(window, window.app);
