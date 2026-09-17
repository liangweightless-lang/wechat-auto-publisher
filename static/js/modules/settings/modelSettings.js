// 大模型运行时动态配置抽屉模块 (Dynamic LLM Provider & Model Switcher)
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';
import { BottomSheet } from '../../components/BottomSheet.js';

let modelSettingsDrawer = null;

// 预设主流大模型提供商配置
const PROVIDER_PRESETS = {
    zhipu: {
        name: '智谱清言 (官方永久免费)',
        baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
        model: 'glm-4-flash',
        docUrl: 'https://bigmodel.cn/',
        tip: '清华智谱官方声明 GLM-4-Flash 永久完全免费，注册即送 Key，终身不限 Token、零充值门槛。'
    },
    siliconflow: {
        name: '硅基流动 SiliconFlow',
        baseUrl: 'https://api.siliconflow.cn/v1',
        model: 'deepseek-ai/DeepSeek-R1',
        docUrl: 'https://cloud.siliconflow.cn/',
        tip: '新用户注册免费送 14~20 元体验金（约 2000 万 Token），满血 DeepSeek-R1 深度思考。'
    },
    deepseek: {
        name: 'DeepSeek 官方 API',
        baseUrl: 'https://api.deepseek.com/v1',
        model: 'deepseek-chat',
        docUrl: 'https://platform.deepseek.com/',
        tip: '深度求索官方开放平台，支持 deepseek-chat (V3) 与 deepseek-reasoner (R1)。'
    },
    custom: {
        name: '自定义 OpenAI 协议端点',
        baseUrl: '',
        model: '',
        docUrl: '',
        tip: '支持任何兼容 OpenAI /v1/chat/completions 格式的本地 Ollama、OneAPI 或第三方中转服务。'
    }
};

export function initModelSettingsDrawer() {
    if (modelSettingsDrawer) return modelSettingsDrawer;

    modelSettingsDrawer = new BottomSheet({
        id: 'modelSettingsSheet',
        title: '大模型与推理集群动态配置',
        subtitle: '支持在线热切智谱永久免费模型、硅基流动与 DeepSeek，秒级热生效',
        icon: 'cpu',
        maxHeight: '88vh',
        renderBody: renderModelSettingsLayout,
        onOpen: () => {
            loadCurrentModelConfig();
        }
    });

    return modelSettingsDrawer;
}

export function openModelSettingsDrawer() {
    const drawer = initModelSettingsDrawer();
    drawer.open();
}

export function closeModelSettingsDrawer() {
    if (modelSettingsDrawer) modelSettingsDrawer.close();
}

function renderModelSettingsLayout() {
    return `
    <div style="display: flex; flex-direction: column; gap: 14px; padding-bottom: 20px;">
        
        <!-- 1. 推荐免费与主流服务商快捷切换卡片 -->
        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px;">
            <div style="font-size: 12.5px; font-weight: 700; color: var(--text-main); margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                <i data-lucide="sparkles" style="width: 13px; height: 13px; color: #f59e0b;"></i>
                <span>选择大模型服务商预设</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;" id="providerPresetsGrid">
                <button type="button" class="category-pill active" onclick="window.app.applyModelPreset('zhipu', this)" style="justify-content: center; padding: 8px 10px; font-size: 12px; border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.08); color: #059669;">
                    <span style="font-weight: 700;">🌟 智谱 GLM-4 (永久免费)</span>
                </button>
                <button type="button" class="category-pill" onclick="window.app.applyModelPreset('siliconflow', this)" style="justify-content: center; padding: 8px 10px; font-size: 12px;">
                    <span>⚡ 硅基流动 SiliconFlow</span>
                </button>
                <button type="button" class="category-pill" onclick="window.app.applyModelPreset('deepseek', this)" style="justify-content: center; padding: 8px 10px; font-size: 12px;">
                    <span>🤖 DeepSeek 官方</span>
                </button>
                <button type="button" class="category-pill" onclick="window.app.applyModelPreset('custom', this)" style="justify-content: center; padding: 8px 10px; font-size: 12px;">
                    <span>🌐 自定义 OpenAI 端点</span>
                </button>
            </div>
            <div id="providerTipBox" style="font-size: 11.5px; color: var(--text-light); line-height: 1.45; margin-top: 10px; padding: 8px 10px; background: var(--bg-hover); border-radius: 6px; border-left: 3px solid #10b981;">
                清华智谱官方声明 GLM-4-Flash 永久完全免费，注册即送 Key，终身不限 Token、零充值门槛。
            </div>
        </div>

        <!-- 2. 具体配置表单 -->
        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: flex; flex-direction: column; gap: 12px;">
            <div>
                <label style="display: block; font-size: 12px; font-weight: 600; color: var(--text-main); margin-bottom: 5px;">
                    API 接口地址 (Base URL)
                </label>
                <input type="text" id="cfgBaseUrl" class="mobile-text-input" placeholder="例如: https://open.bigmodel.cn/api/paas/v4" style="width: 100%; font-size: 12.5px; font-family: monospace;">
            </div>

            <div>
                <label style="display: block; font-size: 12px; font-weight: 600; color: var(--text-main); margin-bottom: 5px;">
                    模型标识 (Model Identifier)
                </label>
                <input type="text" id="cfgModelName" class="mobile-text-input" placeholder="例如: glm-4-flash 或 deepseek-ai/DeepSeek-R1" style="width: 100%; font-size: 12.5px; font-family: monospace;">
                <div style="display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap;">
                    <span class="kw-tag" onclick="document.getElementById('cfgModelName').value='glm-4-flash'" style="cursor: pointer; font-size: 10.5px;">glm-4-flash (智谱免费)</span>
                    <span class="kw-tag" onclick="document.getElementById('cfgModelName').value='deepseek-ai/DeepSeek-R1'" style="cursor: pointer; font-size: 10.5px;">DeepSeek-R1 (深度思考)</span>
                    <span class="kw-tag" onclick="document.getElementById('cfgModelName').value='Qwen/Qwen2.5-7B-Instruct'" style="cursor: pointer; font-size: 10.5px;">Qwen2.5-7B (极速秒出)</span>
                </div>
            </div>

            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <label style="font-size: 12px; font-weight: 600; color: var(--text-main);">
                        API 密钥 (API Key)
                    </label>
                    <span id="cfgKeyStatus" style="font-size: 11px; color: #10b981;">已载入</span>
                </div>
                <div style="position: relative;">
                    <input type="password" id="cfgApiKey" class="mobile-text-input" placeholder="输入新的 API Key（留空则保持现有密钥不变）" style="width: 100%; font-size: 12.5px; font-family: monospace; padding-right: 36px;">
                    <button type="button" onclick="window.app.toggleKeyVisibility()" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--text-light); cursor: pointer; padding: 4px;">
                        <i data-lucide="eye" id="keyVisIcon" style="width: 14px; height: 14px;"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- 3. 测试连通性状态面板 -->
        <div id="testResultBox" style="display: none; padding: 10px 12px; border-radius: 6px; font-size: 12px; line-height: 1.45;"></div>

        <!-- 4. 操作按钮区 -->
        <div style="display: flex; gap: 10px; margin-top: 4px;">
            <button type="button" id="btnTestLlm" class="category-pill" onclick="window.app.testModelConnection()" style="flex: 1; justify-content: center; padding: 10px; font-size: 12.5px; border-color: var(--border);">
                <i data-lucide="activity" style="width: 14px; height: 14px;"></i>
                <span id="btnTestText">测试连通性</span>
            </button>
            <button type="button" id="btnSaveLlm" class="theme-chip active" onclick="window.app.saveModelConfig()" style="flex: 1.4; justify-content: center; padding: 10px; font-size: 13px; font-weight: 700; background: var(--primary); color: #ffffff;">
                <i data-lucide="save" style="width: 14px; height: 14px;"></i>
                <span>保存并即刻热生效</span>
            </button>
        </div>

    </div>
    `;
}

// 载入当前运行态配置
export async function loadCurrentModelConfig() {
    try {
        const resp = await fetch('/api/settings/llm');
        const data = await resp.json();
        if (data && data.code === 200) {
            const baseUrlEl = document.getElementById('cfgBaseUrl');
            const modelEl = document.getElementById('cfgModelName');
            const keyStatusEl = document.getElementById('cfgKeyStatus');

            if (baseUrlEl) baseUrlEl.value = data.base_url || '';
            if (modelEl) modelEl.value = data.model || '';
            if (keyStatusEl) {
                if (data.has_api_key) {
                    keyStatusEl.innerHTML = `<span style="color: #10b981;">当前密钥: ${data.masked_api_key}</span>`;
                } else {
                    keyStatusEl.innerHTML = `<span style="color: #ef4444;">未设置密钥</span>`;
                }
            }

            // 自动高亮匹配预设按钮
            const provider = data.provider || 'siliconflow';
            highlightPresetBtn(provider);
        }
    } catch (e) {
        console.warn('获取大模型配置失败:', e);
    }
}

// 应用预设配置
export function applyModelPreset(presetKey, btnEl) {
    const preset = PROVIDER_PRESETS[presetKey];
    if (!preset) return;

    highlightPresetBtn(presetKey);

    const baseUrlEl = document.getElementById('cfgBaseUrl');
    const modelEl = document.getElementById('cfgModelName');
    const tipBox = document.getElementById('providerTipBox');

    if (baseUrlEl && preset.baseUrl) baseUrlEl.value = preset.baseUrl;
    if (modelEl && preset.model) modelEl.value = preset.model;
    if (tipBox) {
        tipBox.innerHTML = `
            ${preset.tip}
            ${preset.docUrl ? `<a href="${preset.docUrl}" target="_blank" style="color: var(--primary); font-weight: 600; text-decoration: none; margin-left: 6px;">打开平台官网获取 Key ↗</a>` : ''}
        `;
    }
}

function highlightPresetBtn(presetKey) {
    document.querySelectorAll('#providerPresetsGrid .category-pill').forEach(b => {
        b.classList.remove('active');
        b.style.borderColor = 'var(--border)';
        b.style.background = 'transparent';
        b.style.color = 'var(--text-main)';
    });

    const activeBtn = document.querySelector(`#providerPresetsGrid button[onclick*="'${presetKey}'"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        activeBtn.style.background = 'rgba(16, 185, 129, 0.08)';
        activeBtn.style.color = '#059669';
    }
}

// 切换密码明文查看
export function toggleKeyVisibility() {
    const input = document.getElementById('cfgApiKey');
    const icon = document.getElementById('keyVisIcon');
    if (!input) return;

    if (input.type === 'password') {
        input.type = 'text';
        if (icon) icon.setAttribute('data-lucide', 'eye-off');
    } else {
        input.type = 'password';
        if (icon) icon.setAttribute('data-lucide', 'eye');
    }
    refreshIcons();
}

// 测试连通性
export async function testModelConnection() {
    const baseUrl = document.getElementById('cfgBaseUrl')?.value.trim();
    const model = document.getElementById('cfgModelName')?.value.trim();
    const apiKey = document.getElementById('cfgApiKey')?.value.trim();
    const box = document.getElementById('testResultBox');
    const btnText = document.getElementById('btnTestText');

    if (!baseUrl || !model) {
        showToast('请先填写 Base URL 与 Model 标识', 'warning');
        return;
    }

    if (btnText) btnText.innerText = '测试连通中...';
    if (box) {
        box.style.display = 'block';
        box.style.background = 'rgba(59, 130, 246, 0.08)';
        box.style.border = '1px solid rgba(59, 130, 246, 0.2)';
        box.style.color = '#2563eb';
        box.innerHTML = '<i data-lucide="loader-2" class="spin-icon" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i> 正在向大模型集群发送微型探活请求...';
        refreshIcons();
    }

    try {
        const resp = await fetch('/api/settings/llm/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ base_url: baseUrl, model, api_key: apiKey })
        });
        const res = await resp.json();

        if (res.code === 200) {
            box.style.background = 'rgba(16, 185, 129, 0.08)';
            box.style.border = '1px solid rgba(16, 185, 129, 0.3)';
            box.style.color = '#059669';
            box.innerHTML = `✅ <b>模型连通成功！</b> 响应耗时: ${res.latency}，回包正常: "${res.reply}"`;
            showToast('大模型握手成功！', 'success');
        } else {
            box.style.background = 'rgba(239, 68, 68, 0.08)';
            box.style.border = '1px solid rgba(239, 68, 68, 0.3)';
            box.style.color = '#dc2626';
            box.innerHTML = `❌ <b>连接未通过:</b> ${res.message}`;
            showToast(res.message, 'error');
        }
    } catch (e) {
        if (box) {
            box.style.background = 'rgba(239, 68, 68, 0.08)';
            box.style.border = '1px solid rgba(239, 68, 68, 0.3)';
            box.style.color = '#dc2626';
            box.innerHTML = `❌ <b>请求异常:</b> ${e.message}`;
        }
    } finally {
        if (btnText) btnText.innerText = '测试连通性';
        refreshIcons();
    }
}

// 保存配置
export async function saveModelConfig() {
    const baseUrl = document.getElementById('cfgBaseUrl')?.value.trim();
    const model = document.getElementById('cfgModelName')?.value.trim();
    const apiKey = document.getElementById('cfgApiKey')?.value.trim();

    if (!baseUrl || !model) {
        showToast('Base URL 与 Model 标识不能为空', 'warning');
        return;
    }

    // 识别当前 provider
    let provider = 'custom';
    if (baseUrl.includes('bigmodel.cn')) provider = 'zhipu';
    else if (baseUrl.includes('siliconflow')) provider = 'siliconflow';
    else if (baseUrl.includes('deepseek')) provider = 'deepseek';

    try {
        const resp = await fetch('/api/settings/llm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider,
                base_url: baseUrl,
                model,
                api_key: apiKey
            })
        });
        const res = await resp.json();
        if (res.code === 200) {
            showToast('大模型配置已成功更新并即刻生效！', 'success');
            const keyInput = document.getElementById('cfgApiKey');
            if (keyInput) keyInput.value = '';
            loadCurrentModelConfig();
            setTimeout(() => {
                closeModelSettingsDrawer();
            }, 800);
        } else {
            showToast(`保存失败: ${res.message}`, 'error');
        }
    } catch (e) {
        showToast(`保存异常: ${e.message}`, 'error');
    }
}
