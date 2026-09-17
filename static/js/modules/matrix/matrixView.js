import { state } from '../../store/state.js';
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';

export function switchPlatform(platform) {
    state.currentActivePlatform = platform;

    // 胶囊高亮
    const wechatBtn = document.getElementById('tabBtnWechat');
    const douyinBtn = document.getElementById('tabBtnDouyin');
    const xhsBtn = document.getElementById('tabBtnXiaohongshu');
    if (wechatBtn) wechatBtn.classList.toggle('active', platform === 'wechat');
    if (douyinBtn) douyinBtn.classList.toggle('active', platform === 'douyin');
    if (xhsBtn) xhsBtn.classList.toggle('active', platform === 'xiaohongshu');

    // 面板切换
    const paneW = document.getElementById('paneWechat');
    const paneD = document.getElementById('paneDouyin');
    const paneX = document.getElementById('paneXiaohongshu');
    if (paneW) paneW.classList.toggle('active', platform === 'wechat');
    if (paneD) paneD.classList.toggle('active', platform === 'douyin');
    if (paneX) paneX.classList.toggle('active', platform === 'xiaohongshu');

    // 换肤栏仅微信可用
    const quickBar = document.getElementById('themeQuickBar');
    if (quickBar) quickBar.style.display = platform === 'wechat' ? 'flex' : 'none';

    // 底部动作按钮
    const pubBtn = document.getElementById('mobilePublishBtn');
    const pubText = document.getElementById('mobilePubText');
    const pubIcon = document.getElementById('mobilePubIcon');

    if (pubBtn && pubText) {
        if (platform === 'wechat') {
            pubBtn.style.background = '#07c160';
            pubText.innerText = '一键推送到微信公众号草稿箱';
            if (pubIcon) pubIcon.setAttribute('data-lucide', 'send');
        } else if (platform === 'douyin') {
            pubBtn.style.background = 'linear-gradient(135deg, #1e1e2e, #11111b)';
            pubText.innerText = '📋 一键复制抖音短视频脚本';
            if (pubIcon) pubIcon.setAttribute('data-lucide', 'copy');
        } else if (platform === 'xiaohongshu') {
            pubBtn.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
            pubText.innerText = '📋 一键复制小红书爆款笔记';
            if (pubIcon) pubIcon.setAttribute('data-lucide', 'copy');
        }
    }
    refreshIcons();
}

export function copyActiveContent() {
    let content = '';
    let name = '';
    if (state.currentActivePlatform === 'wechat') {
        const previewBox = document.getElementById('previewHtmlBody');
        content = previewBox ? previewBox.innerText : '';
        name = '微信长文';
    } else if (state.currentActivePlatform === 'douyin') {
        const dy = document.getElementById('matrixDouyinText');
        content = dy ? dy.innerText : '';
        name = '抖音短视频脚本';
    } else if (state.currentActivePlatform === 'xiaohongshu') {
        const xhs = document.getElementById('matrixXiaohongshuText');
        content = xhs ? xhs.innerText : '';
        name = '小红书图文笔记';
    }

    if (!content) {
        showToast('当前暂无可复制的内容', 'warning');
        return;
    }

    navigator.clipboard.writeText(content).then(() => {
        showToast(`已成功复制${name}到剪贴板！`, 'success');
    }).catch(() => {
        showToast('复制失败，请手动长按复制', 'error');
    });
}
