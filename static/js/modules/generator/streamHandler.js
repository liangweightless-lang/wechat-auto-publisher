import { state } from '../../store/state.js';
import { showToast } from '../../utils/toast.js';
import { refreshIcons } from '../../utils/dom.js';

export function closeProgressModal() {
    const modal = document.getElementById('progressModal');
    if (modal) modal.classList.remove('active');

    const genBtn = document.getElementById('mobileGenBtn');
    const genSpinner = document.getElementById('mobileGenSpinner');
    const genIcon = document.getElementById('mobileGenIcon');
    const genText = document.getElementById('mobileGenText');
    if (genBtn) genBtn.disabled = false;
    if (genSpinner) genSpinner.style.display = 'none';
    if (genIcon) genIcon.style.display = 'inline-block';
    if (genText) genText.innerText = '开始深度研判并生成推文';

    if (state.totalTimerInterval) {
        clearInterval(state.totalTimerInterval);
        state.totalTimerInterval = null;
    }
}

export function toggleThinking() {
    state.isThinkingCollapsed = !state.isThinkingCollapsed;
    const box = document.getElementById('thinkingText');
    const arrow = document.getElementById('thinkingArrow');
    if (box) {
        box.style.display = state.isThinkingCollapsed ? 'none' : 'block';
    }
    if (arrow) {
        arrow.setAttribute('data-lucide', state.isThinkingCollapsed ? 'chevron-right' : 'chevron-down');
        refreshIcons();
    }
}

export function setStepActive(stepNum) {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById('step' + i);
        if (!el) continue;
        if (i < stepNum) {
            el.className = 'step-chip done';
        } else if (i === stepNum) {
            el.className = 'step-chip active';
        } else {
            el.className = 'step-chip';
        }
    }
}

export async function triggerMobileGenerate() {
    const topicInput = document.getElementById('mobileTopicInput');
    const topic = topicInput ? topicInput.value.trim() : '';

    if (!topic && !state.selectedFile) {
        showToast('请先勾选热点情报或输入研判线索', 'warning');
        return;
    }

    const genBtn = document.getElementById('mobileGenBtn');
    const genSpinner = document.getElementById('mobileGenSpinner');
    const genIcon = document.getElementById('mobileGenIcon');
    const genText = document.getElementById('mobileGenText');
    const modal = document.getElementById('progressModal');
    const thinkingText = document.getElementById('thinkingText');
    const streamText = document.getElementById('streamText');
    const statusMsg = document.getElementById('streamStatusMsg');
    const wordCountEl = document.getElementById('streamWordCount');
    const timerLabel = document.getElementById('totalTimer');

    // UI 状态重置
    if (genBtn) genBtn.disabled = true;
    if (genSpinner) genSpinner.style.display = 'block';
    if (genIcon) genIcon.style.display = 'none';
    if (genText) genText.innerText = '战局推演与长文撰写中...';
    if (modal) modal.classList.add('active');

    if (thinkingText) thinkingText.innerText = '';
    if (streamText) streamText.innerText = '';
    if (statusMsg) statusMsg.innerText = '正在启动智库推演引擎，组织多源战报...';
    if (wordCountEl) wordCountEl.innerText = '已生成 0 字';
    setStepActive(1);

    state.startTime = Date.now();
    if (state.totalTimerInterval) clearInterval(state.totalTimerInterval);
    state.totalTimerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
        if (timerLabel) timerLabel.innerText = `耗时 ${elapsed}s`;
    }, 1000);

    const formData = new FormData();
    if (topic) formData.append('topic', topic);
    if (state.selectedFile) formData.append('file', state.selectedFile);

    if (state.selectedArticlesMap.size > 0) {
        const articlesList = Array.from(state.selectedArticlesMap.values());
        formData.append('selected_articles', JSON.stringify(articlesList));
    }

    const themeVal = document.getElementById('themeSelect') ? document.getElementById('themeSelect').value : 'think_tank';
    const styleVal = document.getElementById('imageStyleSelect') ? document.getElementById('imageStyleSelect').value : 'photojournalism';
    formData.append('theme', themeVal);
    formData.append('image_style', styleVal);

    try {
        const response = await fetch('/api/generate/stream', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split('\n\n');
            buffer = events.pop();

            for (const ev of events) {
                if (!ev.trim()) continue;

                let eventType = 'message';
                let eventData = '';

                const lines = ev.split('\n');
                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        eventType = line.replace('event: ', '').trim();
                    } else if (line.startsWith('data: ')) {
                        eventData = line.replace('data: ', '').trim();
                    }
                }

                if (!eventData) continue;
                let dataObj = null;
                try {
                    dataObj = JSON.parse(eventData);
                } catch (e) {
                    continue;
                }

                if (eventType === 'status') {
                    if (statusMsg) statusMsg.innerText = dataObj.message || '';
                    if (dataObj.message && dataObj.message.includes('配图')) {
                        setStepActive(4);
                    } else if (dataObj.message && dataObj.message.includes('排版')) {
                        setStepActive(5);
                    }
                } else if (eventType === 'think') {
                    setStepActive(2);
                    if (thinkingText) {
                        thinkingText.innerText += dataObj.text || '';
                        thinkingText.scrollTop = thinkingText.scrollHeight;
                    }
                } else if (eventType === 'content') {
                    setStepActive(3);
                    // 自动折叠思考链，将全部高度留给长文阅读
                    const thinkingBox = document.getElementById('thinkingText');
                    const thinkingArrow = document.getElementById('thinkingArrow');
                    if (thinkingBox && !thinkingBox.classList.contains('collapsed')) {
                        thinkingBox.classList.add('collapsed');
                        if (thinkingArrow) thinkingArrow.style.transform = 'rotate(-90deg)';
                    }
                    if (streamText) {
                        streamText.innerText += dataObj.text || '';
                        streamText.scrollTop = streamText.scrollHeight;
                        const charLen = streamText.innerText.replace(/\s+/g, '').length;
                        if (wordCountEl) wordCountEl.innerText = `已生成 ${charLen} 字`;
                    }
                } else if (eventType === 'done') {
                    state.isGenerationCompleted = true;
                    setStepActive(5);
                    try {
                        if (reader && reader.cancel) await reader.cancel();
                    } catch (_) {}
                    try {
                        handleGenerationDone(dataObj);
                    } catch (doneErr) {
                        console.error('handleGenerationDone 处理异常:', doneErr);
                        const modal = document.getElementById('progressModal');
                        if (modal) modal.classList.remove('active');
                        if (window.app && window.app.switchMainTab) window.app.switchMainTab('matrix');
                    }
                    return;
                } else if (eventType === 'error') {
                    showToast(dataObj.message || '生成中断', 'error');
                    if (statusMsg) {
                        statusMsg.innerHTML = `<span style="color: #ef4444; font-weight: 600;">推演异常: ${dataObj.message}</span> <button onclick="window.app.closeProgressModal()" style="margin-left: 8px; padding: 2px 10px; border-radius: 4px; background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 11px; cursor: pointer;">关闭返回</button>`;
                    }
                    return;
                }
            }
        }
    } catch (e) {
        if (state.isGenerationCompleted || e.name === 'AbortError') {
            console.log('推演已正常完成或安全释放流连接');
            return;
        }
        showToast('生成请求异常: ' + e.message, 'error');
        if (statusMsg) {
            statusMsg.innerHTML = `<span style="color: #ef4444; font-weight: 600;">推演中断: ${e.message}</span> <button onclick="window.app.closeProgressModal()" style="margin-left: 8px; padding: 2px 10px; border-radius: 4px; background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 11px; cursor: pointer;">关闭返回</button>`;
        }
    } finally {
        if (genBtn) genBtn.disabled = false;
        if (genSpinner) genSpinner.style.display = 'none';
        if (genIcon) genIcon.style.display = 'inline-block';
        if (genText) genText.innerText = '开始深度研判并生成推文';
        if (state.totalTimerInterval) clearInterval(state.totalTimerInterval);
    }
}

export function handleGenerationDone(data) {
    state.currentGeneratedData = data;

    const mockTitle = document.getElementById('previewMockTitle');
    if (mockTitle && data.title) mockTitle.innerText = data.title;

    const previewBody = document.getElementById('mobilePreviewContent');
    if (previewBody) {
        previewBody.innerHTML = data.wechat_html || data.html_content || '<p>研报排版完成</p>';
    }

    const dyEl = document.getElementById('douyinScriptText');
    if (dyEl) dyEl.value = data.douyin_script || '暂无矩阵脚本';

    const xhsEl = document.getElementById('xiaohongshuNoteText');
    if (xhsEl) xhsEl.value = data.xiaohongshu_note || '暂无小红书图文笔记';

    // 隐藏进度弹层并停止计时器
    if (state.totalTimerInterval) {
        clearInterval(state.totalTimerInterval);
        state.totalTimerInterval = null;
    }
    const modal = document.getElementById('progressModal');
    if (modal) modal.classList.remove('active');

    // 自动平滑切换到矩阵排版 Tab
    try {
        if (window.app && window.app.switchMainTab) {
            window.app.switchMainTab('matrix');
        }
    } catch (tabErr) {
        console.warn('切换矩阵排版Tab微弱异常:', tabErr);
    }

    showToast('智库深度研报生成完毕！', 'success');
}
