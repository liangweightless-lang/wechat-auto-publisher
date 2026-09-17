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
        <!-- 今日雷达胶囊区 (支持手动增删与 AI 自动推演) -->
        <div class="strategy-radar-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12.5px; font-weight: 700; color: var(--primary); display: inline-flex; align-items: center; gap: 5px;">
                    <i data-lucide="crosshair" style="width: 14px; height: 14px;"></i>
                    <span>情报抓取雷达词库</span>
                    <span id="strategyKeywordCount" style="font-size: 10.5px; font-weight: 600; padding: 1px 6px; border-radius: 10px; background: rgba(37,99,235,0.1); color: var(--primary);">0</span>
                </span>
                <button class="select-all-btn" id="btnAiRadarRefresh" type="button" style="font-size: 11px; padding: 3px 9px; display: inline-flex; align-items: center; gap: 4px;" title="基于今日前沿战报，AI 智能提炼最新雷达词">
                    <i data-lucide="sparkles" style="width: 11px; height: 11px;"></i>
                    <span>AI 智能推演</span>
                </button>
            </div>
            
            <!-- 雷达词动态列表 (支持独立删除) -->
            <div id="strategyActiveKeywords" style="display: flex; flex-wrap: wrap; gap: 6px; min-height: 28px; align-items: center;">
                <span style="font-size: 11px; color: var(--text-light);">加载雷达词库中...</span>
            </div>

            <!-- 手动快速添加关键词栏 -->
            <div style="display: flex; gap: 6px; margin-top: 10px; align-items: center;">
                <input type="text" id="manualKeywordInput" placeholder="+ 输入自定义关键词手动添加 (如: 歼-35A, 萨德系统)" style="flex: 1; height: 32px; border-radius: 6px; border: 1px dashed var(--border); padding: 0 10px; font-size: 12px; background: var(--bg-surface); color: var(--text-main); outline: none;" />
                <button type="button" id="btnAddManualKeyword" onclick="window.app.addManualKeyword()" style="height: 32px; padding: 0 12px; border-radius: 6px; background: var(--primary); color: #fff; border: none; font-size: 12px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 3px;">
                    <i data-lucide="plus" style="width: 13px; height: 13px;"></i>
                    <span>添加</span>
                </button>
            </div>

            <div id="strategySummaryDesc" style="font-size: 11.5px; color: var(--text-muted); margin-top: 8px; line-height: 1.4;"></div>
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
        } else if (e.target && e.target.id === 'manualKeywordInput' && e.key === 'Enter') {
            e.preventDefault();
            addManualKeyword();
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

export function updateHomeRadarBar(keywords) {
    const container = document.getElementById('todayRadarKeywords');
    if (!container || !Array.isArray(keywords) || keywords.length === 0) return;
    container.innerHTML = keywords.map(kw => `
        <span class="today-radar-kw-chip">${kw}</span>
    `).join('');
}

export async function syncTodayRadarToHome() {
    try {
        const data = await strategyApi.getCurrentStrategy();
        if (data && data.strategy && data.strategy.active_keywords) {
            updateHomeRadarBar(data.strategy.active_keywords);
        }
    } catch (e) {
        console.error("同步首页雷达词失败:", e);
    }
}

function renderStrategyContent(strategy) {
    if (strategy && strategy.active_keywords) {
        updateHomeRadarBar(strategy.active_keywords);
    }
    const countBadge = document.getElementById('strategyKeywordCount');
    const radarContainer = document.getElementById('strategyActiveKeywords');
    if (radarContainer) {
        const kws = strategy.active_keywords || [];
        if (countBadge) countBadge.innerText = kws.length;

        if (kws.length === 0) {
            radarContainer.innerHTML = '<span style="font-size: 11.5px; color: var(--text-muted);">暂无雷达词，请在下方手动添加或点击上方“AI 智能推演”</span>';
        } else {
            radarContainer.innerHTML = kws.map(kw => `
                <span class="radar-kw-pill" style="display: inline-flex; align-items: center; gap: 4px; padding: 3px 6px 3px 8px; border-radius: 6px; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.2); font-size: 11.5px; color: var(--text-main); font-weight: 500;">
                    <i data-lucide="crosshair" style="width: 10px; height: 10px; color: var(--primary);"></i>
                    <span>${kw}</span>
                    <button type="button" onclick="window.app.removeManualKeyword('${kw}', event)" style="background: transparent; border: none; padding: 0 2px; cursor: pointer; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; border-radius: 3px; transition: all 0.15s ease;" onmouseover="this.style.color='#ef4444'; this.style.background='rgba(239,68,68,0.1)'" onmouseout="this.style.color='var(--text-muted)'; this.style.background='transparent'" title="删除该雷达词">
                        <i data-lucide="x" style="width: 11px; height: 11px;"></i>
                    </button>
                </span>
            `).join('');
        }
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
                <div class="msg-avatar ${msg.role === 'user' ? 'user' : 'assistant'}"><i data-lucide="${msg.role === 'user' ? 'user' : 'shield'}" style="width: 13px; height: 13px;"></i></div>
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
                <div class="msg-avatar user"><i data-lucide="user" style="width: 13px; height: 13px;"></i></div>
                <div class="msg-bubble"><div class="msg-text">${escapeStrategyHtml(msg)}</div></div>
            </div>
            <div class="strategy-msg-item assistant" id="strategyThinkingBubble">
                <div class="msg-avatar assistant"><i data-lucide="shield" style="width: 13px; height: 13px;"></i></div>
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
    showToast('AI 正在根据今日国际战局推演最新雷达词...', 'info');
    try {
        const sampleTitles = (state.currentClustersData || []).map(c => c.main_title);
        const res = await strategyApi.refreshRadar(sampleTitles);
        if (res && res.active_keywords) {
            if (state.currentStrategy) {
                state.currentStrategy.active_keywords = res.active_keywords;
                renderStrategyContent(state.currentStrategy);
            }
            showToast(`AI 已成功刷新 ${res.active_keywords.length} 个今日防务雷达词！`, 'success');
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
            showToast('已恢复为初始标准智库策略', 'info');
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

/**
 * 手动添加雷达关键词
 */
export async function addManualKeyword() {
    const input = document.getElementById('manualKeywordInput');
    if (!input) return;
    const kw = input.value.trim();
    if (!kw) {
        showToast('请输入关键词名称', 'warning');
        return;
    }

    try {
        const res = await strategyApi.updateKeywords('add', kw);
        if (res && res.code === 200) {
            input.value = '';
            if (state.currentStrategy) {
                state.currentStrategy.active_keywords = res.active_keywords;
                renderStrategyContent(state.currentStrategy);
            }
            updateHomeRadarBar(res.active_keywords);
            showToast(`已成功添加雷达词: ${kw}`, 'success');
        } else {
            showToast(res.message || '添加失败', 'error');
        }
    } catch (e) {
        showToast('添加雷达词异常: ' + e.message, 'error');
    }
}

/**
 * 手动删除指定雷达关键词
 */
export async function removeManualKeyword(kw, event) {
    if (event) event.stopPropagation();
    if (!kw) return;

    try {
        const res = await strategyApi.updateKeywords('remove', kw);
        if (res && res.code === 200) {
            if (state.currentStrategy) {
                state.currentStrategy.active_keywords = res.active_keywords;
                renderStrategyContent(state.currentStrategy);
            }
            updateHomeRadarBar(res.active_keywords);
            showToast(`已移除雷达词: ${kw}`, 'info');
        } else {
            showToast(res.message || '移除失败', 'error');
        }
    } catch (e) {
        showToast('移除雷达词异常: ' + e.message, 'error');
    }
}
