// 前端企业级主入口 (Enterprise Main App Entry)
import { state } from './store/state.js';
import { refreshIcons } from './utils/dom.js';
import { showToast } from './utils/toast.js';
import { initTheme, toggleTheme } from './modules/theme/themeManager.js';
import { fetchAndRenderTopics, toggleCluster, expandOfficialSources } from './modules/topics/topicCards.js';
import { toggleSelectNews, selectAllInCluster, selectTopic, updateSelectedUI } from './modules/topics/topicSelector.js';
import { triggerMobileGenerate, toggleThinking } from './modules/generator/streamHandler.js';
import { switchPlatform, copyActiveContent } from './modules/matrix/matrixView.js';
import { openHistoryDrawer, closeHistoryDrawer, loadHistoryArticles, loadHistoryArticleDetail, showSourceNewsModal } from './modules/history/historyView.js';
import { openStrategyDrawer, closeStrategyDrawer, loadStrategyData, sendStrategyTuneMessage, triggerAiRadarRefresh, resetStrategyToDefault } from './modules/strategy/strategyChat.js';
import { openPromptDrawer, closePromptDrawer, loadPromptConfig, savePrompts, resetPrompts } from './modules/prompt/promptConfig.js';
import { publishApi } from './api/publishApi.js';

// 统一抽屉路由分配 (Decoupled Drawer Router)
export function openBottomSheet(sheetId) {
    if (sheetId === 'strategySheet') {
        openStrategyDrawer();
    } else if (sheetId === 'historySheet') {
        openHistoryDrawer();
    } else if (sheetId === 'promptSheet') {
        openPromptDrawer();
    }
}

export function closeBottomSheet(sheetId) {
    if (sheetId === 'strategySheet') {
        closeStrategyDrawer();
    } else if (sheetId === 'historySheet') {
        closeHistoryDrawer();
    } else if (sheetId === 'promptSheet') {
        closePromptDrawer();
    }
}

// 页面主 Tab 切换 (发现选题 / 矩阵排版)
export function switchMainTab(tabName) {
    const viewTopics = document.getElementById('tabViewTopics');
    const viewMatrix = document.getElementById('tabViewMatrix');
    const btnTopics = document.getElementById('tabNavTopics');
    const btnMatrix = document.getElementById('tabNavMatrix');
    const dock = document.getElementById('multiSelectDock');

    if (tabName === 'topics') {
        if (viewTopics) viewTopics.classList.add('active');
        if (viewMatrix) viewMatrix.classList.remove('active');
        if (btnTopics) btnTopics.classList.add('active');
        if (btnMatrix) btnMatrix.classList.remove('active');
        if (dock && state.selectedArticlesMap.size > 0) {
            dock.classList.add('active');
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (tabName === 'matrix' || tabName === 'preview') {
        if (viewMatrix) viewMatrix.classList.add('active');
        if (viewTopics) viewTopics.classList.remove('active');
        if (btnMatrix) btnMatrix.classList.add('active');
        if (btnTopics) btnTopics.classList.remove('active');
        if (dock) dock.classList.remove('active');

        const badge = document.getElementById('previewDot');
        if (badge) badge.classList.remove('active');
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
export function handleMobileFile(input) {
    if (input.files && input.files[0]) {
        state.selectedFile = input.files[0];
        const label = document.getElementById('mobileFileLabel');
        if (label) {
            label.innerText = `📎 ${state.selectedFile.name.substring(0, 10)}...`;
            label.style.color = 'var(--primary)';
        }
        showToast(`📄 报告已挂载: ${state.selectedFile.name}`, 'success');
    }
}

export function clearTopicInput() {
    const input = document.getElementById('mobileTopicInput');
    if (input) {
        input.value = '';
        input.style.height = 'auto';
        input.style.borderColor = 'var(--border)';
    }
    state.selectedArticlesMap.clear();
    updateSelectedUI();
    showToast('已清空选题内容与选中的情报', 'info');
}

// 触发多选生成
export function triggerMultiSelectGenerate() {
    triggerMobileGenerate();
}

// 快速换肤与重排
export async function switchThemeQuick(themeKey, btnEl) {
    document.querySelectorAll('.theme-quick-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    const previewBody = document.getElementById('mobilePreviewContent');
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

// 全局命名空间挂载，确保原生 HTML 属性无缝调用
window.app = {
    openBottomSheet,
    closeBottomSheet,
    openStrategyDrawer,
    closeStrategyDrawer,
    openHistoryDrawer,
    closeHistoryDrawer,
    openPromptDrawer,
    closePromptDrawer,
    switchMainTab,
    selectCategory,
    refreshCurrentFeed,
    toggleCluster,
    toggleSelectNews,
    selectAllInCluster,
    selectTopic,
    handleMobileFile,
    clearTopicInput,
    triggerMultiSelectGenerate,
    expandOfficialSources,
    triggerMobileGenerate,
    toggleThinking,
    switchPlatform,
    copyActiveContent,
    triggerMobilePublish,
    switchThemeQuick,
    loadHistoryArticles,
    loadHistoryArticleDetail,
    showSourceNewsModal,
    sendStrategyTuneMessage,
    triggerAiRadarRefresh,
    resetStrategyToDefault,
    loadPromptConfig,
    savePrompts,
    resetPrompts,
    toggleTheme,
    refreshIcons
};

Object.assign(window, window.app);

// 页面加载生命周期
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    refreshIcons();
    fetchAndRenderTopics('all', false);
});
