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
            pubText.innerText = '一键复制抖音短视频脚本';
            if (pubIcon) pubIcon.setAttribute('data-lucide', 'copy');
        } else if (platform === 'xiaohongshu') {
            pubBtn.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
            pubText.innerText = '一键复制小红书爆款笔记';
            if (pubIcon) pubIcon.setAttribute('data-lucide', 'copy');
        }
    }
    refreshIcons();
}

/**
 * 全平台极速兼容复制引擎 (支持微信图文富文本内联样式与全浏览器剪贴板)
 */
export function copyActiveContent() {
    const platform = state.currentActivePlatform;
    let htmlContent = '';
    let plainContent = '';
    let platformName = '内容';

    if (platform === 'wechat') {
        platformName = '微信排版图文';
        const previewBox = document.getElementById('mobilePreviewContent');
        if (!previewBox) {
            showToast('未找到可复制的排版内容', 'warning');
            return;
        }
        htmlContent = previewBox.innerHTML;
        plainContent = previewBox.innerText;
    } else if (platform === 'douyin') {
        platformName = '抖音解说脚本';
        const dy = document.getElementById('douyinScriptText');
        plainContent = dy ? dy.value : '';
        htmlContent = plainContent.replace(/\n/g, '<br>');
    } else if (platform === 'xiaohongshu') {
        platformName = '小红书图文笔记';
        const xhs = document.getElementById('xiaohongshuNoteText');
        plainContent = xhs ? xhs.value : '';
        htmlContent = plainContent.replace(/\n/g, '<br>');
    }

    if (!plainContent && !htmlContent) {
        showToast('当前暂无可复制的内容，请先生成推文', 'warning');
        return;
    }

    // 优先采用工业级富文本剪贴板注入（支持直接粘贴到微信公众平台草稿箱，带全部颜色、图片和样式）
    const success = copyRichTextToClipboard(htmlContent, plainContent);
    if (success) {
        showToast(`已成功复制${platformName}（富文本样式已保留，可直接粘贴进微信后台）`, 'success');
    } else {
        // 若同步选区失败，尝试异步 Clipboard API 兜底
        if (navigator.clipboard && window.isSecureContext) {
            const blobHtml = new Blob([htmlContent], { type: 'text/html' });
            const blobText = new Blob([plainContent], { type: 'text/plain' });
            const item = new ClipboardItem({
                'text/html': blobHtml,
                'text/plain': blobText
            });
            navigator.clipboard.write([item]).then(() => {
                showToast(`已成功复制${platformName}到剪贴板！`, 'success');
            }).catch(() => {
                showToast('复制异常，请长按页面文本进行选择复制', 'error');
            });
        } else {
            showToast('复制失败，请手动在预览区长按全选复制', 'error');
        }
    }
}

/**
 * 工业级 DOM 选区与剪贴板事件注入 (解决 HTTP 非安全上下文与移动端复制失效问题)
 */
function copyRichTextToClipboard(html, plain) {
    let succeeded = false;

    const onCopyHandler = (e) => {
        try {
            e.clipboardData.setData('text/html', html);
            e.clipboardData.setData('text/plain', plain);
            e.preventDefault();
            succeeded = true;
        } catch (err) {
            console.warn('[Clipboard]: setData 写入异常:', err);
        }
    };

    document.addEventListener('copy', onCopyHandler);

    try {
        // 创建不可见的临时容器作为选区锚点
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.left = '-9999px';
        container.style.top = '0';
        container.style.opacity = '0';
        container.setAttribute('contenteditable', 'true');
        container.innerHTML = html;
        document.body.appendChild(container);

        container.focus();
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(container);
        selection.removeAllRanges();
        selection.addRange(range);

        succeeded = document.execCommand('copy');
        selection.removeAllRanges();
        document.body.removeChild(container);
    } catch (err) {
        console.warn('[Clipboard]: execCommand 选区复制异常:', err);
    } finally {
        document.removeEventListener('copy', onCopyHandler);
    }

    return succeeded;
}
