import { state } from '../../store/state.js';
import { strategyApi } from '../../api/strategyApi.js';
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';
import { openBottomSheet, closeBottomSheet } from '../theme/themeManager.js';

export async function loadStrategyData() {
    try {
        const data = await strategyApi.getCurrentStrategy();
        if (data && data.strategy) {
            state.currentStrategy = data.strategy;
            renderStrategyUI(data.strategy);
        }
    } catch (e) {
        console.error("加载智库策略异常:", e);
    }
}

export function renderStrategyUI(strategy) {
    // 1. 渲染活跃关键词雷达胶囊
    const radarContainer = document.getElementById('strategyActiveKeywords');
    if (radarContainer) {
        const kws = strategy.active_keywords || [];
        radarContainer.innerHTML = kws.map(kw => `
            <span class="radar-kw-pill">
                <i data-lucide="crosshair" style="width: 10px; height: 10px;"></i>
                <span>${kw}</span>
            </span>
        `).join('');
    }

    // 2. 渲染策略简要描述
    const summaryEl = document.getElementById('strategySummaryDesc');
    if (summaryEl) {
        summaryEl.textContent = strategy.focus_summary || '覆盖中东、俄乌、红海及台海四大垂直体系防务动态。';
    }

    // 3. 渲染对话历史
    const chatBox = document.getElementById('strategyChatMessages');
    if (chatBox) {
        const history = strategy.chat_history || [];
        chatBox.innerHTML = history.map(msg => `
            <div class="strategy-msg-item ${msg.role === 'user' ? 'user' : 'assistant'}">
                <div class="msg-avatar">
                    ${msg.role === 'user' ? '👤' : '🛡️'}
                </div>
                <div class="msg-bubble">
                    <div class="msg-text">${escapeStrategyHtml(msg.content)}</div>
                </div>
            </div>
        `).join('');
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    refreshIcons();
}

export async function sendStrategyTuneMessage() {
    const input = document.getElementById('strategyChatInput');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    const chatBox = document.getElementById('strategyChatMessages');

    // 立即在前端追加用户消息
    if (chatBox) {
        chatBox.innerHTML += `
            <div class="strategy-msg-item user">
                <div class="msg-avatar">👤</div>
                <div class="msg-bubble"><div class="msg-text">${escapeStrategyHtml(msg)}</div></div>
            </div>
            <div class="strategy-msg-item assistant" id="strategyThinkingBubble">
                <div class="msg-avatar">🛡️</div>
                <div class="msg-bubble">
                    <div class="msg-text" style="display: flex; align-items: center; gap: 6px; color: var(--text-light);">
                        <i data-lucide="loader-2" class="spin" style="width: 13px; height: 13px;"></i>
                        <span>正在为您调优抓取雷达与研报侧重...</span>
                    </div>
                </div>
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;
        refreshIcons();
    }

    try {
        const res = await strategyApi.chatTune(msg);
        const thinkingEl = document.getElementById('strategyThinkingBubble');
        if (thinkingEl) thinkingEl.remove();

        if (res && res.reply) {
            state.currentStrategy = res.strategy;
            renderStrategyUI(res.strategy);
            showToast('✅ 策略已即时更新并持久化生效！', 'success');
        }
    } catch (e) {
        const thinkingEl = document.getElementById('strategyThinkingBubble');
        if (thinkingEl) {
            thinkingEl.querySelector('.msg-text').innerHTML = `<span style="color: #ef4444;">策略调整异常: ${e.message}</span>`;
        }
        showToast('策略调整异常，请重试', 'error');
    }
}

export async function triggerAiRadarRefresh() {
    showToast('🧠 AI 正在根据今日国际战局推演最新雷达词...', 'info');
    try {
        const sampleTitles = (state.currentClustersData || []).map(c => c.main_title);
        const res = await strategyApi.refreshRadar(sampleTitles);
        if (res && res.active_keywords) {
            if (state.currentStrategy) {
                state.currentStrategy.active_keywords = res.active_keywords;
                renderStrategyUI(state.currentStrategy);
            }
            showToast(`🎯 AI 已成功刷新 ${res.active_keywords.length} 个今日防务雷达词！`, 'success');
        }
    } catch (e) {
        showToast('AI 刷新雷达词异常', 'error');
    }
}

export async function resetStrategyToDefault() {
    if (!confirm('确定要重置为初始标准智库策略吗？')) return;
    try {
        const res = await strategyApi.resetStrategy();
        if (res && res.strategy) {
            state.currentStrategy = res.strategy;
            renderStrategyUI(res.strategy);
            showToast('🔄 已恢复为初始标准智库策略', 'info');
        }
    } catch (e) {
        showToast('重置策略失败', 'error');
    }
}

function escapeStrategyHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br/>');
}
