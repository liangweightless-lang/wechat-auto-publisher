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

    // 动态渲染已并网情报源卡片
    const mergedCard = document.getElementById('mergedSourcesInfoCard');
    if (mergedCard) {
        if (state.selectedArticlesMap.size > 0) {
            const list = Array.from(state.selectedArticlesMap.values());
            mergedCard.style.display = 'block';
            mergedCard.innerHTML = `
                <div style="font-weight: 700; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between; color: var(--primary);">
                    <span>🔗 本次推演已并网 ${list.length} 份战报信源：</span>
                    <span style="font-size: 10px; opacity: 0.8; background: rgba(37,99,235,0.15); padding: 1px 5px; border-radius: 3px;">交叉推演中</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 3px; max-height: 75px; overflow-y: auto;">
                    ${list.map((a, idx) => `
                        <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 11px; color: var(--text-main);">
                            ${idx + 1}. [${a.source || '公开战报'}] ${a.title}
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            mergedCard.style.display = 'none';
        }
    }

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
                        const isBalanceError = (dataObj.message && (dataObj.message.includes('402') || dataObj.message.includes('余额') || dataObj.message.includes('insufficient')));
                        statusMsg.innerHTML = `
                            <div style="padding: 12px; border-radius: 10px; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); text-align: left;">
                                <div style="color: #ef4444; font-weight: 600; font-size: 13px; margin-bottom: 6px;">
                                    ⚠️ 推演中断: ${dataObj.message}
                                </div>
                                ${isBalanceError ? `
                                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed rgba(239, 68, 68, 0.2); font-size: 12px; color: var(--text-muted);">
                                    💡 <b>当前平台余额不足</b>：建议切换至<b>智谱 GLM-4-Flash</b> (官方永久免费，不花一分钱)。
                                    <div style="margin-top: 8px; display: flex; gap: 8px;">
                                        <button onclick="window.app.closeProgressModal(); window.app.openBottomSheet('modelSettingsSheet');" style="padding: 6px 14px; border-radius: 6px; background: #10b981; color: #ffffff; border: none; font-size: 12px; font-weight: 700; cursor: pointer;">
                                            ⚙️ 立即打开配置切换免费模型
                                        </button>
                                        <button onclick="window.app.closeProgressModal()" style="padding: 6px 12px; border-radius: 6px; background: var(--bg-surface); color: var(--text-main); border: 1px solid var(--border); font-size: 12px; cursor: pointer;">
                                            关闭
                                        </button>
                                    </div>
                                </div>
                                ` : `
                                <div style="margin-top: 6px;">
                                    <button onclick="window.app.closeProgressModal()" style="padding: 4px 12px; border-radius: 6px; background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 12px; cursor: pointer;">关闭返回</button>
                                </div>
                                `}
                            </div>
                        `;
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
