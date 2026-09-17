/**
 * 局势洞见 · 防务智库发布工作台 前端交互逻辑
 * 支持：DeepSeek-R1 流式深度思考链 (Thinking) + 长文流式输出 + 历史战史检索驱动
 */

let currentTopicData = null;
let selectedFile = null;
let currentTheme = 'light';
let isThinkingCollapsed = false;
let totalTimerInterval = null;
let startTime = 0;

// 1. 初始化
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadHotTopics();
});

// 2. 主题切换 (浅色 / 深色)
function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    setTheme(saved);
}

function toggleTheme() {
    const next = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(next);
}

function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const icon = document.getElementById('themeIcon');
    if (icon) icon.innerText = theme === 'light' ? '☀️' : '🌙';
}

// 3. 标签切换 (编辑 / 预览)
function switchView(tab) {
    const navEdit = document.getElementById('tabNavEdit');
    const navPreview = document.getElementById('tabNavPreview');
    const viewEdit = document.getElementById('viewEdit');
    const viewPreview = document.getElementById('viewPreview');

    if (tab === 'edit') {
        navEdit.classList.add('active');
        navPreview.classList.remove('active');
        viewEdit.classList.add('active');
        viewPreview.classList.remove('active');
    } else {
        navPreview.classList.add('active');
        navEdit.classList.remove('active');
        viewPreview.classList.add('active');
        viewEdit.classList.remove('active');
        const dot = document.getElementById('previewDot');
        if (dot) dot.classList.remove('active');
    }
}

// 4. 加载热搜舆情
let currentCategory = 'all';

function selectCategory(cat, el) {
    currentCategory = cat;
    document.querySelectorAll('.tab-chip').forEach(c => c.classList.remove('active'));
    if (el) el.classList.add('active');
    loadHotTopics(cat);
}

async function loadHotTopics(cat = 'all') {
    const listEl = document.getElementById('mobileHotList');
    if (!listEl) return;
    listEl.innerHTML = '<div style="text-align: center; padding: 24px; font-size: 13px; color: var(--text-muted);">正在拉取2026最新战略情报...</div>';

    try {
        const resp = await fetch(`/api/topics?category=${cat}`);
        const data = await resp.json();
        if (data && data.topics && data.topics.length > 0) {
            renderTopics(data.topics);
        } else {
            listEl.innerHTML = '<div style="padding: 24px; color: var(--text-light); text-align: center; font-size: 13px;">当前分类暂无热点，可点击其他分类</div>';
        }
    } catch (e) {
        listEl.innerHTML = '<div style="padding: 24px; color: var(--text-light); text-align: center; font-size: 13px;">网络通信异常，请重试</div>';
    }
}

function renderTopics(topics) {
    const listEl = document.getElementById("mobileHotList");
    if (!listEl) return;
    listEl.innerHTML = "";
    topics.slice(0, 8).forEach((t, idx) => {
        const item = document.createElement("div");
        item.className = "topic-row-item";
        item.onclick = () => selectTopic(t.title);

        const sourceName = t.source || "权威防务信源";
        const jumpUrl = t.url || ("https://www.toutiao.com/search?keyword=" + encodeURIComponent(t.title));
        const isOverseas = !!t.is_overseas;
        const badgeClass = isOverseas ? "topic-badge-overseas" : "topic-badge-tag";
        const badgeIcon = isOverseas ? "🌐" : "📰";
        const pubTime = t.pub_time || "今日最新";

        let summaryHtml = "";
        if (t.summary) {
            summaryHtml = `<div class="topic-abstract">${t.summary}</div>`;
        }

        item.innerHTML = `
            <div class="topic-rank-num">${idx + 1}</div>
            <div class="topic-main-content">
                <div class="topic-top-meta">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="${badgeClass}">${badgeIcon} ${sourceName}</span>
                        <span class="topic-time-tag">🕒 ${pubTime}</span>
                    </div>
                    <a href="${jumpUrl}" target="_blank" rel="noopener noreferrer" class="topic-source-jump" onclick="event.stopPropagation()" title="在浏览器打开新闻出处">
                        <span>出处原文</span>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    </a>
                </div>
                <div class="topic-headline">${t.title}</div>
                ${summaryHtml}
            </div>
        `;
        listEl.appendChild(item);
    });
}

function selectTopic(title) {
    const input = document.getElementById('mobileTopicInput');
    if (input) {
        input.value = title;
        updateCharCount(input);
        showToast('已选取热点，可进一步补充焦点');
    }
}

function updateCharCount(el) {
    const countEl = document.getElementById('charCount');
    if (countEl) countEl.innerText = `${el.value.length} 字`;
}

// 5. 本地文件上传 (PDF/TXT)
function handleMobileFile(input) {
    if (input.files && input.files[0]) {
        selectedFile = input.files[0];
        const label = document.getElementById('mobileFileLabel');
        if (label) label.innerHTML = `已选择报告: <strong>${selectedFile.name}</strong>`;
        showToast('报告已就绪');
    }
}

// 6. 思考链面板展开/收起
function toggleThinking() {
    isThinkingCollapsed = !isThinkingCollapsed;
    const box = document.getElementById('thinkingText');
    const arrow = document.getElementById('thinkingArrow');
    if (box) {
        box.style.display = isThinkingCollapsed ? 'none' : 'block';
    }
    if (arrow) {
        arrow.innerText = isThinkingCollapsed ? '▶' : '▼';
    }
}

function setStepActive(stepNum) {
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

// 7. 流式生成核心调度 (SSE Stream Fetcher)
async function triggerMobileGenerate() {
    const topicInput = document.getElementById('mobileTopicInput');
    const topic = topicInput ? topicInput.value.trim() : '';

    if (!topic && !selectedFile) {
        showToast('请先选择热点、输入研判线索或上传智库报告', 'warning');
        return;
    }

    const genBtn = document.getElementById('mobileGenBtn');
    const genSpinner = document.getElementById('mobileGenSpinner');
    const genText = document.getElementById('mobileGenText');
    const modal = document.getElementById('progressModal');
    const thinkingText = document.getElementById('thinkingText');
    const streamText = document.getElementById('streamText');
    const statusMsg = document.getElementById('streamStatusMsg');
    const wordCountEl = document.getElementById('streamWordCount');
    const timerLabel = document.getElementById('totalTimer');
    const thinkingTimeLabel = document.getElementById('thinkingTimeLabel');

    // 初始化 UI 状态
    genBtn.disabled = true;
    if (genSpinner) genSpinner.style.display = 'block';
    if (genText) genText.innerText = '战略推演与生成中...';
    modal.classList.add('active');

    thinkingText.innerText = '';
    streamText.innerText = '';
    statusMsg.innerText = '正在启动智库推演引擎，检索历史档案...';
    wordCountEl.innerText = '已生成 0 字';
    setStepActive(1);

    // 启动全局计时器
    startTime = Date.now();
    if (totalTimerInterval) clearInterval(totalTimerInterval);
    totalTimerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (timerLabel) timerLabel.innerText = `耗时 ${elapsed}s`;
    }, 1000);

    const formData = new FormData();
    if (topic) formData.append('topic', topic);
    if (selectedFile) formData.append('file', selectedFile);
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
            throw new Error(`服务请求失败: HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let currentEvent = 'message';
        let generatedContent = '';
        let thinkingContent = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split(String.fromCharCode(10));
            buffer = lines.pop();

            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) continue;

                if (trimmed.startsWith('event:')) {
                    currentEvent = trimmed.replace('event:', '').trim();
                    continue;
                }

                if (trimmed.startsWith('data:')) {
                    const dataStr = trimmed.replace('data:', '').trim();
                    let payload;
                    try {
                        payload = JSON.parse(dataStr);
                    } catch (err) {
                        continue;
                    }

                    if (currentEvent === 'status') {
                        statusMsg.innerText = payload.message || '';
                        if (payload.message && payload.message.includes('战史')) {
                            setStepActive(1);
                        } else if (payload.message && payload.message.includes('配图')) {
                            setStepActive(4);
                        }
                    } else if (currentEvent === 'think') {
                        setStepActive(2);
                        thinkingContent += payload.text || '';
                        thinkingText.innerText = thinkingContent;
                        thinkingText.scrollTop = thinkingText.scrollHeight;
                        const elapsed = Math.floor((Date.now() - startTime) / 1000);
                        if (thinkingTimeLabel) thinkingTimeLabel.innerText = `推演中 (${elapsed}s)...`;
                    } else if (currentEvent === 'content') {
                        setStepActive(3);
                        if (thinkingTimeLabel && thinkingTimeLabel.innerText.includes('推演中')) {
                            const thinkSec = Math.floor((Date.now() - startTime) / 1000);
                            thinkingTimeLabel.innerText = `已深度思考 (${thinkSec}s)`;
                        }
                        generatedContent += payload.text || '';
                        streamText.innerText = generatedContent;
                        streamText.scrollTop = streamText.scrollHeight;
                        wordCountEl.innerText = `已生成 ${generatedContent.length} 字`;
                    } else if (currentEvent === 'done') {
                        setStepActive(5);
                        clearInterval(totalTimerInterval);
                        currentTopicData = payload;

                        renderPreview(payload);

                        showToast('🎉 智库深度研判长文生成完毕！');
                        setTimeout(() => {
                            modal.classList.remove('active');
                            switchView('preview');
                        }, 800);
                    } else if (currentEvent === 'error') {
                        throw new Error(payload.message || '生成中遭遇未知错误');
                    }
                }
            }
        }

    } catch (err) {
        clearInterval(totalTimerInterval);
        showToast(err.message || '生成失败，请重试', 'error');
        modal.classList.remove('active');
    } finally {
        genBtn.disabled = false;
        if (genSpinner) genSpinner.style.display = 'none';
        if (genText) genText.innerText = '🚀 开始深度研判并生成配图';
    }
}

// 8. 渲染 1:1 仿真微信预览
let currentPlatform = 'wechat';

function renderPreview(data) {
    const titleEl = document.getElementById('previewMockTitle');
    const contentEl = document.getElementById('mobilePreviewContent');
    const countEl = document.getElementById('statWordCount');
    const dot = document.getElementById('previewDot');
    const douyinEl = document.getElementById('douyinScriptText');
    const xhsEl = document.getElementById('xiaohongshuNoteText');

    if (titleEl) titleEl.innerText = data.title || '深度防务研判专栏';
    if (contentEl) contentEl.innerHTML = data.html_content || '<p>暂无正文</p>';
    if (douyinEl) douyinEl.value = data.douyin_script || '暂无抖音脚本';
    if (xhsEl) xhsEl.value = data.xiaohongshu_note || '暂无小红书笔记';
    if (countEl) countEl.innerText = `${data.word_count || 0} 字 (矩阵就绪)`;
    if (dot) dot.classList.add('active');
}

function switchPlatform(p) {
    currentPlatform = p;
    document.querySelectorAll('.matrix-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.platform-pane').forEach(p => p.classList.remove('active'));

    const btn = document.getElementById('tabBtn' + p.charAt(0).toUpperCase() + p.slice(1));
    const pane = document.getElementById('pane' + p.charAt(0).toUpperCase() + p.slice(1));
    if (btn) btn.classList.add('active');
    if (pane) pane.classList.add('active');

    // 动态同步底部吸底栏
    const pubBtnText = document.getElementById('mobilePubText');
    if (pubBtnText) {
        if (p === 'wechat') {
            pubBtnText.innerText = '📤 一键推送到微信公众号草稿箱';
        } else if (p === 'douyin') {
            pubBtnText.innerText = '📋 一键复制抖音分镜头脚本';
        } else if (p === 'xiaohongshu') {
            pubBtnText.innerText = '📋 一键复制小红书爆款图文笔记';
        }
    }
}

function copyActiveContent() {
    if (!currentTopicData) {
        showToast('尚未生成内容，请先执行研判生成', 'warning');
        return;
    }

    if (currentPlatform === 'wechat') {
        copyWechatHtml();
    } else if (currentPlatform === 'douyin') {
        const text = document.getElementById('douyinScriptText').value;
        navigator.clipboard.writeText(text).then(() => {
            showToast('🎬 抖音短视频解说脚本已复制！可直接导入剪映口播');
        });
    } else if (currentPlatform === 'xiaohongshu') {
        const text = document.getElementById('xiaohongshuNoteText').value;
        navigator.clipboard.writeText(text).then(() => {
            showToast('📕 小红书爆款图文笔记已复制！已带Emoji与标签');
        });
    }
}

function copyWechatHtml() {
    const content = document.getElementById('mobilePreviewContent');
    if (!content || content.innerText.includes('暂无生成内容')) {
        showToast('暂无可复制的内容', 'warning');
        return;
    }
    try {
        const blob = new Blob([content.innerHTML], { type: 'text/html' });
        const textBlob = new Blob([content.innerText], { type: 'text/plain' });
        const item = new ClipboardItem({ 'text/html': blob, 'text/plain': textBlob });
        navigator.clipboard.write([item]).then(() => {
            showToast('📋 微信富文本已复制！可以直接在公众号后台粘贴');
        });
    } catch (e) {
        navigator.clipboard.writeText(content.innerText);
        showToast('已复制纯文本格式内容');
    }
}

// 9. 一键推送到微信草稿箱
async function triggerMobilePublish() {
    if (currentPlatform !== 'wechat') {
        copyActiveContent();
        return;
    }
    if (!currentTopicData) {
        showToast('尚未生成文章内容，请先执行研判生成', 'warning');
        return;
    }

    const pubBtn = document.getElementById('mobilePublishBtn');
    const pubSpinner = document.getElementById('mobilePubSpinner');
    const pubText = document.getElementById('mobilePubText');

    pubBtn.disabled = true;
    if (pubSpinner) pubSpinner.style.display = 'block';
    if (pubText) pubText.innerText = '正在推送到微信公众号草稿箱...';

    try {
        const resp = await fetch('/api/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const res = await resp.json();

        if (res.code === 200) {
            showToast('✅ 成功推送到微信公众号草稿箱！MediaId: ' + (res.media_id || '已生成'));
        } else {
            showToast('推送失败: ' + (res.message || '未知错误'), 'error');
        }
    } catch (e) {
        showToast('推送网络异常: ' + e.message, 'error');
    } finally {
        pubBtn.disabled = false;
        if (pubSpinner) pubSpinner.style.display = 'none';
        if (pubText) pubText.innerText = '📤 一键推送到微信公众号草稿箱';
    }
}

// 10. Toast 弹层
function showToast(msg, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerText = msg;
    toast.style.background = type === 'error' ? 'rgba(239, 68, 68, 0.92)' :
                             type === 'warning' ? 'rgba(245, 158, 11, 0.92)' :
                             'rgba(15, 23, 42, 0.92)';
    toast.className = 'active';
    setTimeout(() => {
        toast.className = '';
    }, 3200);
}

// 11. 隐藏入口：连击标题与快捷键调出 Prompt 配置台
let titleClickCount = 0;
let titleClickTimer = null;

function handleTitleClick() {
    titleClickCount++;
    if (titleClickTimer) clearTimeout(titleClickTimer);
    if (titleClickCount >= 3) {
        titleClickCount = 0;
        openPromptModal();
        showToast("🔓 已进入智库核心 Prompt 配置中枢");
        return;
    }
    titleClickTimer = setTimeout(() => {
        titleClickCount = 0;
    }, 700);
}

document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === "p" || e.key === "P")) {
        e.preventDefault();
        openPromptModal();
    }
});

async function openPromptModal() {
    const modal = document.getElementById("promptModal");
    const sysInput = document.getElementById("systemPromptInput");
    const userInput = document.getElementById("userTemplateInput");

    if (!modal) return;
    modal.classList.add("active");

    try {
        const resp = await fetch("/api/prompts");
        const data = await resp.json();
        if (data.code === 200) {
            if (sysInput) sysInput.value = data.system_prompt || "";
            if (userInput) userInput.value = data.user_prompt_template || "";
        }
    } catch (e) {
        showToast("拉取Prompt配置失败: " + e.message, "error");
    }
}

function closePromptModal() {
    const modal = document.getElementById("promptModal");
    if (modal) modal.classList.remove("active");
}

async function savePromptConfig() {
    const sysInput = document.getElementById("systemPromptInput");
    const userInput = document.getElementById("userTemplateInput");

    const system_prompt = sysInput ? sysInput.value.trim() : "";
    const user_prompt_template = userInput ? userInput.value.trim() : "";

    if (!system_prompt || !user_prompt_template) {
        showToast("提示词内容不能为空", "warning");
        return;
    }

    try {
        const resp = await fetch("/api/prompts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ system_prompt, user_prompt_template })
        });
        const res = await resp.json();
        if (res.code === 200) {
            showToast("✅ Prompt配置已成功保存并立即生效！");
            closePromptModal();
        } else {
            showToast("保存失败: " + res.message, "error");
        }
    } catch (e) {
        showToast("通信异常: " + e.message, "error");
    }
}

async function resetPromptConfig() {
    if (!confirm("确定要恢复官方智库预设的 System Prompt 和 User Template 吗？")) {
        return;
    }

    try {
        const resp = await fetch("/api/prompts/reset", { method: "POST" });
        const res = await resp.json();
        if (res.code === 200) {
            const sysInput = document.getElementById("systemPromptInput");
            const userInput = document.getElementById("userTemplateInput");
            if (sysInput) sysInput.value = res.system_prompt || "";
            if (userInput) userInput.value = res.user_prompt_template || "";
            showToast("🔄 已恢复官方智库预设提示词！");
        }
    } catch (e) {
        showToast("重置失败: " + e.message, "error");
    }
}


// =========================================================================
// 8. 实时换肤、AI 配图重绘与 SQLite 历史文库抽屉
// =========================================================================

let currentGeneratedData = null;

function onGenerationFinished(data) {
    currentGeneratedData = data;
    if (window.lucide) lucide.createIcons();
}

async function switchThemeQuick(themeKey, btnEl) {
    if (!currentGeneratedData || !currentGeneratedData.markdown_content) {
        showToast('请先生成文章后再进行主题换肤', 'warning');
        return;
    }

    document.querySelectorAll('.theme-chip').forEach(c => c.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    showToast('正在实时渲染【' + themeKey + '】微信内联样式...');

    try {
        const resp = await fetch('/api/format/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                markdown: currentGeneratedData.markdown_content,
                theme: themeKey
            })
        });
        const res = await resp.json();
        if (res.code === 200) {
            currentGeneratedData.html_content = res.html;
            const previewBox = document.getElementById('mobilePreviewContent');
            if (previewBox) {
                previewBox.innerHTML = res.html;
            }
            showToast('🎉 排版主题已切换为: ' + themeKey);
        } else {
            showToast('换肤失败: ' + res.message, 'error');
        }
    } catch (e) {
        showToast('换肤通信异常: ' + e.message, 'error');
    }
}

async function triggerRegenerateImage() {
    const styleSelect = document.getElementById('imageStyleSelect');
    const styleKey = styleSelect ? styleSelect.value : 'photojournalism';
    const title = currentGeneratedData ? currentGeneratedData.title : (document.getElementById('mobileTopicInput').value.trim() || '前沿战术推演');

    showToast('🎨 AI 正在按【' + styleKey + '】风格重绘配图与封面...');
    try {
        const resp = await fetch('/api/generate/image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: title,
                style: styleKey
            })
        });
        const res = await resp.json();
        if (res.code === 200) {
            showToast('🎉 封面配图已重绘更新！');
        } else {
            showToast('重绘失败: ' + res.message, 'error');
        }
    } catch (e) {
        showToast('生图通信异常: ' + e.message, 'error');
    }
}

// 打开 SQLite 历史文库抽屉
async function openHistoryDrawer() {
    const drawer = document.getElementById('historyDrawer');
    const mask = document.getElementById('historyDrawerMask');
    if (drawer) drawer.classList.add('active');
    if (mask) mask.classList.add('active');

    const container = document.getElementById('historyListContainer');
    if (!container) return;
    container.innerHTML = '<div style="text-align:center; padding: 40px; color: var(--text-muted);">正在加载 SQLite 历史推文库...</div>';

    try {
        const resp = await fetch('/api/articles/history');
        const data = await resp.json();
        if (data.code === 200 && data.articles && data.articles.length > 0) {
            renderHistoryArticles(data.articles);
        } else {
            container.innerHTML = '<div style="text-align:center; padding: 40px; color: var(--text-muted);">📭 历史文库暂无记录，快去生成第一篇吧！</div>';
        }
    } catch (e) {
        container.innerHTML = '<div style="text-align:center; padding: 40px; color: red;">调阅历史库失败: ' + e.message + '</div>';
    }
    if (window.lucide) lucide.createIcons();
}

function closeHistoryDrawer() {
    const drawer = document.getElementById('historyDrawer');
    const mask = document.getElementById('historyDrawerMask');
    if (drawer) drawer.classList.remove('active');
    if (mask) mask.classList.remove('active');
}

function renderHistoryArticles(articles) {
    const container = document.getElementById('historyListContainer');
    if (!container) return;

    let html = '';
    articles.forEach(art => {
        const isPublished = art.publish_status === 'published';
        const statusBadge = isPublished
            ? '<span style="color: #16a34a; font-weight: 600;">✅ 已推送草稿箱</span>'
            : '<span style="color: #ca8a04; font-weight: 600;">📝 草稿存档</span>';

        html += `
        <div class="history-card" onclick="loadHistoryArticle(${art.id})">
            <div class="history-card-header">
                <span class="history-card-tag">${art.category || '研判报告'}</span>
                <span class="history-card-time">${art.created_at || ''}</span>
            </div>
            <div class="history-card-title">${art.title}</div>
            <div class="history-card-status">
                <span>${statusBadge}</span>
                <span>·</span>
                <span>主题: ${art.theme || 'think_tank'}</span>
            </div>
        </div>
        `;
    });
    container.innerHTML = html;
}

async function loadHistoryArticle(id) {
    showToast('正在从 SQLite 恢复推文与矩阵资产...');
    closeHistoryDrawer();

    try {
        const resp = await fetch('/api/articles/get?id=' + id);
        const data = await resp.json();
        if (data.code === 200 && data.article) {
            const art = data.article;
            currentGeneratedData = {
                title: art.title,
                digest: art.lead,
                markdown_content: art.markdown_content,
                html_content: art.wechat_html,
                douyin_script: art.douyin_script,
                xiaohongshu_note: art.xiaohongshu_note,
                cover_image: art.cover_image_path
            };

            // 渲染标题
            const mockTitle = document.getElementById('previewMockTitle');
            if (mockTitle) mockTitle.innerText = art.title;

            // 渲染微信 HTML
            const previewBox = document.getElementById('mobilePreviewContent');
            if (previewBox) previewBox.innerHTML = art.wechat_html;

            // 渲染矩阵短脚本
            const douyinText = document.getElementById('douyinScriptText');
            if (douyinText) douyinText.value = art.douyin_script || '';

            const xhsText = document.getElementById('xiaohongshuNoteText');
            if (xhsText) xhsText.value = art.xiaohongshu_note || '';

            // 更新字数
            const statWord = document.getElementById('statWordCount');
            if (statWord) {
                const words = (art.markdown_content || '').length;
                statWord.innerText = words + ' 字 (耗时 ' + Math.max(1, Math.round(words/380)) + '分钟)';
            }

            // 切换到预览视图
            switchView('preview');
            showToast('🎉 已成功载入历史文章：《' + art.title + '》');
        }
    } catch (e) {
        showToast('调阅文章详情失败: ' + e.message, 'error');
    }
}
