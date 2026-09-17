// 前端企业级主入口 (Enterprise Main App Entry)
import { state } from './store/state.js';
import { refreshIcons } from './utils/dom.js';
import { showToast } from './utils/toast.js';
import { initTheme, toggleTheme } from './modules/theme/themeManager.js';
import { fetchAndRenderTopics, toggleCluster, expandOfficialSources, filterByDynamicCategory, renderDynamicCategories } from './modules/topics/topicCards.js';
import { toggleSelectNews, selectAllInCluster, selectTopic, updateSelectedUI } from './modules/topics/topicSelector.js';
import { triggerMobileGenerate, toggleThinking, closeProgressModal } from './modules/generator/streamHandler.js';
import { switchPlatform, copyActiveContent } from './modules/matrix/matrixView.js';
import { openHistoryDrawer, closeHistoryDrawer, loadHistoryArticles, loadHistoryArticleDetail, showSourceNewsModal } from './modules/history/historyView.js';
import { openStrategyDrawer, closeStrategyDrawer, loadStrategyData, sendStrategyTuneMessage, triggerAiRadarRefresh, resetStrategyToDefault, syncTodayRadarToHome } from './modules/strategy/strategyChat.js';
import { openPromptDrawer, closePromptDrawer, loadPromptConfig, savePrompts, resetPrompts } from './modules/prompt/promptConfig.js';
import { openModelSettingsDrawer, closeModelSettingsDrawer, applyModelPreset, toggleKeyVisibility, testModelConnection, saveModelConfig, loadCurrentModelConfig } from './modules/settings/modelSettings.js';
import { initAuth, showLoginModal, hideLoginModal, toggleAuthPwdVisibility, handleLoginSubmit, toggleUserDropdownMenu, triggerLogout, openChangePwdModal } from './modules/auth/authModal.js';
import { publishApi } from './api/publishApi.js';

// 统一抽屉路由分配 (Decoupled Drawer Router)
export function openBottomSheet(sheetId) {
    if (sheetId === 'strategySheet') {
        openStrategyDrawer();
    } else if (sheetId === 'historySheet') {
        openHistoryDrawer();
    } else if (sheetId === 'promptSheet') {
        openPromptDrawer();
    } else if (sheetId === 'modelSettingsSheet') {
        openModelSettingsDrawer();
    }
}

export function closeBottomSheet(sheetId) {
    if (sheetId === 'strategySheet') {
        closeStrategyDrawer();
    } else if (sheetId === 'historySheet') {
        closeHistoryDrawer();
    } else if (sheetId === 'promptSheet') {
        closePromptDrawer();
    } else if (sheetId === 'modelSettingsSheet') {
        closeModelSettingsDrawer();
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
    filterByDynamicCategory(cat, el);
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
            const fn = state.selectedFile.name; label.innerText = fn.length > 8 ? fn.substring(0, 8) + '...' : fn;
            label.style.color = 'var(--primary)';
        }
        showToast(`素材已挂载: ${state.selectedFile.name}`, 'success');
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

// 标题微型气泡提示 (支持移动端轻触与桌面端悬浮)
export function showTitleBubble(event, el) {
    if (event) event.stopPropagation();
    const fullText = (el.getAttribute('data-full-title') || el.getAttribute('title') || el.innerText || '').trim();
    if (!fullText) return;

    let bubble = document.getElementById('globalTitleBubble');
    if (!bubble) {
        bubble = document.createElement('div');
        bubble.id = 'globalTitleBubble';
        bubble.className = 'title-floating-bubble';
        document.body.appendChild(bubble);
    }

    bubble.innerText = fullText;
    const rect = el.getBoundingClientRect();
    const bubbleTop = Math.max(12, rect.top - 10);
    const bubbleLeft = Math.min(window.innerWidth - 18, Math.max(18, rect.left + rect.width / 2));

    bubble.style.left = `${bubbleLeft}px`;
    bubble.style.top = `${bubbleTop}px`;
    bubble.classList.add('visible');

    if (window._bubbleTimeout) clearTimeout(window._bubbleTimeout);
    window._bubbleTimeout = setTimeout(() => {
        bubble.classList.remove('visible');
    }, 3200);
}

// 快速换肤与重排 (彻底防止格式残缺，支持传递完整 markdown 与 title)
export async function switchThemeQuick(themeKey, btnEl) {
    document.querySelectorAll('.theme-chip, .theme-quick-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    const previewBody = document.getElementById('mobilePreviewContent');
    const md = state.currentGeneratedData?.markdown_content || '';
    const title = state.currentGeneratedData?.title || '';

    if (!previewBody || (!previewBody.innerHTML.trim() && !md)) {
        showToast('请先生成文章后再切换视觉排版', 'warning');
        return;
    }

    showToast('正在实时重新内联排版...', 'info');

    try {
        const res = await publishApi.formatPreview(themeKey, md, title);
        if (res && res.code === 200 && res.html) {
            previewBody.innerHTML = res.html;
            if (state.currentGeneratedData) {
                state.currentGeneratedData.html_content = res.html;
                state.currentGeneratedData.wechat_html = res.html;
                state.currentGeneratedData.theme = themeKey;
            }
            showToast(`已成功切换为【${themeKey}】排版风格`, 'success');
        } else {
            showToast(`换肤失败: ${res?.message || '内容格式异常'}`, 'error');
        }
    } catch (e) {
        showToast(`换肤异常: ${e.message}`, 'error');
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
            showToast(`已成功推送到微信公众平台草稿箱！Media ID: ${res.media_id ? res.media_id.substring(0, 10) : '已就绪'}`, 'success');
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
    initAuth,
    showLoginModal,
    hideLoginModal,
    toggleAuthPwdVisibility,
    handleLoginSubmit,
    toggleUserDropdownMenu,
    triggerLogout,
    openChangePwdModal,
    openModelSettingsDrawer,
    closeModelSettingsDrawer,
    applyModelPreset,
    toggleKeyVisibility,
    testModelConnection,
    saveModelConfig,
    loadCurrentModelConfig,
    switchMainTab,
    selectCategory,
    filterByDynamicCategory,
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
    closeProgressModal,
    switchPlatform,
    copyActiveContent,
    triggerMobilePublish,
    switchThemeQuick,
    showTitleBubble,
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
    initAuth();
    document.addEventListener('click', () => { const b = document.getElementById('globalTitleBubble'); if (b) b.classList.remove('visible'); });
    refreshIcons();
    fetchAndRenderTopics('all', false);
    syncTodayRadarToHome();
});
