// 智库 Prompt 配置自闭环组件 (Self-contained Prompt Drawer Component)
import { BottomSheet } from '../../components/BottomSheet.js';
import { showToast } from '../../utils/toast.js';

let promptDrawer = null;

export function initPromptDrawer() {
    if (promptDrawer) return promptDrawer;

    promptDrawer = new BottomSheet({
        id: 'promptSheet',
        title: '智库研判 Prompt 配置',
        subtitle: `${new Date().getFullYear()}年战时时间坐标锚定与四步研判法则（热更新实时生效）`,
        icon: 'sliders-horizontal',
        renderBody: renderPromptLayout,
        onOpen: loadPromptConfig
    });

    _bindEvents();
    return promptDrawer;
}

export function openPromptDrawer() {
    const drawer = initPromptDrawer();
    drawer.open();
}

export function closePromptDrawer() {
    if (promptDrawer) promptDrawer.close();
}

function renderPromptLayout() {
    return `
    <div style="display: flex; flex-direction: column; gap: 14px;">
        <div class="sheet-field-group">
            <label class="sheet-field-label">
                <i data-lucide="shield" style="width: 14px; height: 14px; color: var(--primary);"></i>
                <span>核心系统设定 (System Prompt)</span>
            </label>
            <textarea class="sheet-textarea" id="cfgSystemPrompt" rows="6" placeholder="正在读取配置..."></textarea>
        </div>
        <div class="sheet-field-group">
            <label class="sheet-field-label">
                <i data-lucide="file-code" style="width: 14px; height: 14px; color: var(--primary);"></i>
                <span>用户研判指令模板 (User Template)</span>
            </label>
            <textarea class="sheet-textarea" id="cfgUserPromptTemplate" rows="7" placeholder="正在读取配置..."></textarea>
        </div>
        <div class="sheet-btn-row">
            <button class="sheet-btn-secondary" id="btnResetPrompts" type="button">
                <i data-lucide="rotate-ccw" style="width: 14px; height: 14px;"></i>
                <span>恢复默认</span>
            </button>
            <button class="sheet-btn-primary" id="btnSavePrompts" type="button">
                <i data-lucide="save" style="width: 14px; height: 14px;"></i>
                <span>保存配置</span>
            </button>
        </div>
    </div>
    `;
}

function _bindEvents() {
    document.addEventListener('click', (e) => {
        if (e.target.closest('#btnResetPrompts')) {
            resetPrompts();
        } else if (e.target.closest('#btnSavePrompts')) {
            savePrompts();
        }
    });
}

export async function loadPromptConfig() {
    try {
        const resp = await fetch('/api/prompts');
        const data = await resp.json();
        if (data.code === 200) {
            const sys = document.getElementById('cfgSystemPrompt');
            const user = document.getElementById('cfgUserPromptTemplate');
            if (sys) sys.value = data.system_prompt || '';
            if (user) user.value = data.user_prompt_template || '';
        }
    } catch (e) {
        showToast('读取 Prompt 异常: ' + e.message, 'error');
    }
}

export async function savePrompts() {
    const sysEl = document.getElementById('cfgSystemPrompt');
    const userEl = document.getElementById('cfgUserPromptTemplate');
    if (!sysEl || !userEl) return;

    try {
        const resp = await fetch('/api/prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                system_prompt: sysEl.value,
                user_prompt_template: userEl.value
            })
        });
        const data = await resp.json();
        if (data.code === 200) {
            showToast('✅ 智库研判 Prompt 配置已保存并实时生效！', 'success');
            closePromptDrawer();
        } else {
            showToast('保存失败: ' + data.message, 'error');
        }
    } catch (e) {
        showToast('保存异常: ' + e.message, 'error');
    }
}

export async function resetPrompts() {
    if (!confirm('确定要重置为初始出厂防务智库 Prompt 设定吗？')) return;
    try {
        const resp = await fetch('/api/prompts/reset', { method: 'POST' });
        const data = await resp.json();
        if (data.code === 200) {
            showToast('已恢复出厂标准 Prompt 设定！', 'info');
            loadPromptConfig();
        }
    } catch (e) {
        showToast('重置异常', 'error');
    }
}
