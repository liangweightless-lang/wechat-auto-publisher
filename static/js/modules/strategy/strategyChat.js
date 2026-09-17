// AI 智库策略总监对话工作台模块 (Self-contained Strategy Chat Component)
import { state } from '../../store/state.js';
import { strategyApi } from '../../api/strategyApi.js';
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';
import { BottomSheet } from '../../components/BottomSheet.js';

let strategyDrawer = null;

// 初始化自包含的策略抽屉
export function initStrategyDrawer() {
    if (strategyDrawer) return strategyDrawer;

    strategyDrawer = new BottomSheet({
        id: 'strategySheet',
        title: 'AI 智库策略总监',
        subtitle: '像与豆包/GPT 对话一样实时优化抓取与文章风格',
        icon: 'bot',
        maxHeight: '85vh',
        renderBody: renderStrategyLayout,
        onOpen: () => {
            loadStrategyData();
            setTimeout(() => {
                const input = document.getElementById('strategyChatInput');
                if (input) input.focus();
            }, 300);
        }
    });

    _bindInternalEvents();
    return strategyDrawer;
}

export function openStrategyDrawer() {
    const drawer = initStrategyDrawer();
    drawer.open();
}

export function closeStrategyDrawer() {
    if (strategyDrawer) strategyDrawer.close();
}

// 内部模板渲染
function renderStrategyLayout() {
    return `
    <div style="display: flex; flex-direction: column; gap: 12px; height: 100%;">
        <!-- 今日雷达胶囊区 -->
        <div class="strategy-radar-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 12px; font-weight: 600; color: var(--primary); display: inline-flex; align-items: center; gap: 4px;">
                    <i data-lucide="crosshair" style="width: 13px; height: 13px;"></i> 今日动态抓取雷达词
                </span>
                <button class="select-all-btn" id="btnAiRadarRefresh" type="button" style="font-size: 11px; padding: 2px 8px;">
                    <i data-lucide="sparkles" style="width: 11px; height: 11px;"></i> AI 自动推演
                </button>
            </div>
            <div id="strategyActiveKeywords" style="display: flex; flex-wrap: wrap; gap: 6px;">
                <span style="font-size: 11px; color: var(--text-light);">加载雷达词库中...</span>
            </div>
            <div id="strategySummaryDesc" style="font-size: 11.5px; color: var(--text-light); margin-top: 8px; line-height: 1.4;"></div>
        </div>

        <!-- 对话消息区 -->
        <div id="strategyChatMessages" class="strategy-chat-container" style="flex: 1; min-height: 240px; max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 4px;">
            <div style="text-align: center; color: var(--text-light); font-size: 12px; padding: 20px;">正在连接智库策略总监...</div>
        </div>

        <!-- 底部输入栏 -->
        <div class="strategy-input-bar" style="display: flex; gap: 8px; align-items: center; padding-top: 8px; border-top: 1px solid var(--border);">
            <input type="text" id="strategyChatInput" placeholder="输入调优指令 (如: 今天重点追踪波兰边境反导, 标题要有紧迫感)" style="flex: 1; height: 38px; border-radius: 8px; border: 1px solid var(--border); padding: 0 12px; font-size: 13px; background: var(--bg-hover); color: var(--text);" />
            <button class="primary-btn" id="btnStrategySend" type="button" style="height: 38px; padding: 0 14px; border-radius: 8px; font-size: 13px; display: inline-flex; align-items: center; gap: 4px; background: var(--primary); color: white; border: none; cursor: pointer;">
                <i data-lucide="send" style="width: 13px; height: 13px;"></i>
                <span>发送</span>
            </button>
            <button class="reset-btn" id="btnStrategyReset" type="button" title="恢复默认策略" style="height: 38px; width: 38px; border-radius: 8px; border: 1px solid var(--border); background: transparent; color: var(--text-light); display: flex; align-items: center; justify-content: center; cursor: pointer;">
                <i data-lucide="rotate-ccw" style="width: 14px; height: 14px;"></i>
            </button>
        </div>
    </div>
    `;
}

function _bindInternalEvents() {
    document.addEventListener('click', (e) => {
        if (e.target.closest('#btnAiRadarRefresh')) {
            triggerAiRadarRefresh();
        } else if (e.target.closest('#btnStrategySend')) {
            sendStrategyTuneMessage();
        } else if (e.target.closest('#btnStrategyReset')) {
            resetStrategyToDefault();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.target && e.target.id === 'strategyChatInput' && e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendStrategyTuneMessage();
        }
    });
}

export async function loadStrategyData() {
    try {
        const data = await strategyApi.getCurrentStrategy();
        if (data && data.strategy) {
            state.currentStrategy = data.strategy;
            renderStrategyContent(data.strategy);
        }
    } catch (e) {
        console.error("加载智库策略异常:", e);
    }
}

function renderStrategyContent(strategy) {
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

    const summaryEl = document.getElementById('strategySummaryDesc');
    if (summaryEl) {
        summaryEl.textContent = strategy.focus_summary || '覆盖中东、俄乌、红海及台海四大垂直体系防务动态。';
    }

    const chatBox = document.getElementById('strategyChatMessages');
    if (chatBox) {
        const history = strategy.chat_history || [];
        chatBox.innerHTML = history.map(msg => `
            <div class="strategy-msg-item ${msg.role === 'user' ? 'user' : 'assistant'}">
                <div class="msg-avatar">${msg.role === 'user' ? '👤' : '🛡️'}</div>
                <div class="msg-bubble"><div class="msg-text">${escapeStrategyHtml(msg.content)}</div></div>
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
            renderStrategyContent(res.strategy);
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
                renderStrategyContent(state.currentStrategy);
            }
            showToast(`🎯 AI 已成功刷新 ${res.active_keywords.length} 个今日防务雷达词！`, 'success');
        }
    } catch (e) {
        showToast('AI 刷新雷达词异常', 'error');
    }
}

export async function resetStrategyToDefault() {
    if (!confirm('确定要恢复为初始标准智库策略吗？')) return;
    try {
        const res = await strategyApi.resetStrategy();
        if (res && res.strategy) {
            state.currentStrategy = res.strategy;
            renderStrategyContent(res.strategy);
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
