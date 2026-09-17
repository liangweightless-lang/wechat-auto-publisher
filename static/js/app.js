/**
 * 局势洞见 · 移动原生 App 级交互与数据处理中枢 (V4.0 Mobile Native)
 * 支持：移动端原生 Bottom Tab Bar、Bottom Sheet 手势滑起、DeepSeek-R1 思考流、全量 Lucide 矢量图标
 */

let currentTopicData = null;
let selectedFile = null;
let currentTheme = 'light';
let isThinkingCollapsed = false;
let totalTimerInterval = null;
let startTime = 0;
let currentCategory = 'all';
let currentActivePlatform = 'wechat';
let currentGeneratedData = null;

// =========================================================================
// 1. 初始化与主题管理
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadHotTopics('all');
    loadPromptConfig();
    refreshIcons();
});

function refreshIcons() {
    if (window.lucide) {
        lucide.createIcons();
    }
}

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
    const iconEl = document.getElementById('themeLucideIcon');
    if (iconEl) {
        iconEl.setAttribute('data-lucide', theme === 'light' ? 'sun' : 'moon');
        refreshIcons();
    }
}

// =========================================================================
// 2. iOS 原生底部导航栏切换 (Bottom Navigation Bar)
// =========================================================================
function switchMainTab(tabName) {
    // 隐藏所有主视图
    const viewTopics = document.getElementById('tabViewTopics');
    const viewMatrix = document.getElementById('tabViewMatrix');
    const btnTopics = document.getElementById('tabNavTopics');
    const btnMatrix = document.getElementById('tabNavMatrix');

    if (tabName === 'topics') {
        viewTopics.classList.add('active');
        viewMatrix.classList.remove('active');
        btnTopics.classList.add('active');
        btnMatrix.classList.remove('active');
    } else if (tabName === 'matrix') {
        viewMatrix.classList.add('active');
        viewTopics.classList.remove('active');
        btnMatrix.classList.add('active');
        btnTopics.classList.remove('active');

        // 清除未读红点
        const badge = document.getElementById('previewDot');
        if (badge) badge.classList.remove('active');
    }
    refreshIcons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =========================================================================
// 3. 移动端自底向上滑起面板 (Bottom Sheet)
// =========================================================================
function openBottomSheet(sheetId) {
    const sheet = document.getElementById(sheetId);
    const backdrop = document.getElementById(sheetId + 'Backdrop');
    if (sheet) sheet.classList.add('active');
    if (backdrop) backdrop.classList.add('active');

    if (sheetId === 'historySheet') {
        loadHistoryArticles();
    } else if (sheetId === 'promptSheet') {
        loadPromptConfig();
    }
    refreshIcons();
}

function closeBottomSheet(sheetId) {
    const sheet = document.getElementById(sheetId);
    const backdrop = document.getElementById(sheetId + 'Backdrop');
    if (sheet) sheet.classList.remove('active');
    if (backdrop) backdrop.classList.remove('active');
}

// =========================================================================
// 4. 多源情报榜单分类与拉取
// =========================================================================
function selectCategory(cat, el) {
    currentCategory = cat;
    document.querySelectorAll('.category-pill').forEach(c => c.classList.remove('active'));
    if (el) el.classList.add('active');
    loadHotTopics(cat);
}

async function loadHotTopics(cat = 'all') {
    const listEl = document.getElementById('mobileHotList');
    if (!listEl) return;
    listEl.innerHTML = `
        <div class="feed-empty-state">
            <i data-lucide="loader-2" class="spin-icon" style="width: 20px; height: 20px;"></i>
            <span>正在检索2026战略情报源...</span>
        </div>
    `;
    refreshIcons();

    try {
        const resp = await fetch(`/api/topics?category=${cat}`);
        const data = await resp.json();
        if (data && data.topics && data.topics.length > 0) {
            renderTopics(data.topics);
        } else {
            listEl.innerHTML = `
                <div class="feed-empty-state">
                    <i data-lucide="inbox" style="width: 22px; height: 22px; color: var(--text-light);"></i>
                    <span>暂未拉取到该分类热点，轻点右上角刷新重试</span>
                </div>
            `;
            refreshIcons();
        }
    } catch (e) {
        listEl.innerHTML = `<div class="feed-empty-state" style="color: #ef4444;">拉取失败: ${e.message}</div>`;
    }
}

function renderTopics(topics) {
    const listEl = document.getElementById('mobileHotList');
    if (!listEl) return;

    let html = '';
    topics.forEach((t, idx) => {
        const source = t.source || '官方通报';
        const pubTime = t.pub_time || '刚刚';
        const url = t.url || '';

        html += `
        <div class="topic-item-row" onclick="selectTopic(${idx})">
            <div class="topic-meta-line">
                <span class="source-badge">
                    <i data-lucide="rss" style="width: 10px; height: 10px;"></i>
                    <span>${source}</span>
                </span>
                <span class="time-badge">${pubTime}</span>
            </div>
            <div class="topic-headline">${t.title}</div>
            ${url ? `<div style="text-align: right; margin-top: 2px;"><a href="${url}" target="_blank" onclick="event.stopPropagation()" style="font-size: 10.5px; color: var(--primary); text-decoration: none; display: inline-flex; align-items: center; gap: 2px;"><i data-lucide="external-link" style="width: 10px; height: 10px;"></i>出处原文</a></div>` : ''}
        </div>
        `;
    });

    window._currentTopics = topics;
    listEl.innerHTML = html;
    refreshIcons();
}

function selectTopic(idx) {
    if (!window._currentTopics || !window._currentTopics[idx]) return;
    const t = window._currentTopics[idx];
    currentTopicData = t;

    const input = document.getElementById('mobileTopicInput');
    if (input) {
        input.value = t.title;
        autoResizeTextarea(input);
    }

    // 视觉选中高亮
    const rows = document.querySelectorAll('.topic-item-row');
    rows.forEach((r, i) => {
        if (i === idx) r.classList.add('selected');
        else r.classList.remove('selected');
    });

    showToast('已填入研判焦点: ' + t.title.substring(0, 18) + '...');
}

function clearTopicInput() {
    const input = document.getElementById('mobileTopicInput');
    if (input) {
        input.value = '';
        input.style.height = 'auto';
    }
    const count = document.getElementById('charCount');
    if (count) count.innerText = '0 字';
    document.querySelectorAll('.topic-item-row').forEach(r => r.classList.remove('selected'));
    currentTopicData = null;
}

function autoResizeTextarea(el) {
    el.style.height = 'auto';
    el.style.height = (el.scrollHeight) + 'px';
    const count = document.getElementById('charCount');
    if (count) count.innerText = el.value.length + ' 字';
}

function handleMobileFile(input) {
    if (input.files && input.files[0]) {
        selectedFile = input.files[0];
        const label = document.getElementById('mobileFileLabel');
        if (label) {
            label.innerText = `已就绪: ${selectedFile.name} (${Math.round(selectedFile.size / 1024)} KB)`;
            label.style.color = 'var(--primary)';
        }
        showToast('报告已挂载');
    }
}

// =========================================================================
// 5. 思考链面板展开/收起
// =========================================================================
function toggleThinking() {
    isThinkingCollapsed = !isThinkingCollapsed;
    const box = document.getElementById('thinkingText');
    const arrow = document.getElementById('thinkingArrow');
    if (box) {
        box.style.display = isThinkingCollapsed ? 'none' : 'block';
    }
    if (arrow) {
        arrow.setAttribute('data-lucide', isThinkingCollapsed ? 'chevron-right' : 'chevron-down');
        refreshIcons();
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

// =========================================================================
// 6. 流式生成核心调度 (SSE Stream Fetcher)
// =========================================================================
async function triggerMobileGenerate() {
    const topicInput = document.getElementById('mobileTopicInput');
    const topic = topicInput ? topicInput.value.trim() : '';

    if (!topic && !selectedFile) {
        showToast('请先选择热点、输入研判线索或上传智库报告', 'warning');
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

    // 初始化 UI 状态
    genBtn.disabled = true;
    if (genSpinner) genSpinner.style.display = 'block';
    if (genIcon) genIcon.style.display = 'none';
    if (genText) genText.innerText = '战局推演与生成中...';
    modal.classList.add('active');

    thinkingText.innerText = '';
    streamText.innerText = '';
    statusMsg.innerText = '正在启动智库推演引擎，检索历史档案...';
    wordCountEl.innerText = '已生成 0 字';
    setStepActive(1);

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
                    thinkingText.innerText += dataObj.text || '';
                    thinkingText.scrollTop = thinkingText.scrollHeight;
                } else if (eventType === 'content') {
                    setStepActive(3);
                    streamText.innerText += dataObj.text || '';
                    streamText.scrollTop = streamText.scrollHeight;
                    const charLen = streamText.innerText.replace(/\s+/g, '').length;
                    wordCountEl.innerText = `已生成 ${charLen} 字`;
                } else if (eventType === 'done') {
                    setStepActive(5);
                    handleGenerationDone(dataObj);
                    return;
                } else if (eventType === 'error') {
                    showToast(dataObj.message || '生成中断', 'error');
                    if (statusMsg) statusMsg.innerText = '错误: ' + dataObj.message;
                    return;
                }
            }
        }
    } catch (e) {
        showToast('生成请求异常: ' + e.message, 'error');
        if (statusMsg) statusMsg.innerText = '推演中断: ' + e.message;
    } finally {
        genBtn.disabled = false;
        if (genSpinner) genSpinner.style.display = 'none';
        if (genIcon) genIcon.style.display = 'inline-block';
        if (genText) genText.innerText = '开始深度研判并生成推文';
        if (totalTimerInterval) clearInterval(totalTimerInterval);
    }
}

function handleGenerationDone(data) {
    currentGeneratedData = data;

    // 填入微信长文
    const mockTitle = document.getElementById('previewMockTitle');
    if (mockTitle) mockTitle.innerText = data.title;

    const previewBox = document.getElementById('mobilePreviewContent');
    if (previewBox) previewBox.innerHTML = data.html_content;

    // 填入矩阵短脚本
    const douyinText = document.getElementById('douyinScriptText');
    if (douyinText) douyinText.value = data.douyin_script || '';

    const xhsText = document.getElementById('xiaohongshuNoteText');
    if (xhsText) xhsText.value = data.xiaohongshu_note || '';

    // 更新篇幅统计
    const statWord = document.getElementById('statWordCount');
    if (statWord) {
        statWord.innerText = `${data.word_count || 0} 字 · 预计精读 ${data.read_time || 1} 分钟`;
    }

    // 关闭模态框并切到矩阵预览
    const modal = document.getElementById('progressModal');
    if (modal) modal.classList.remove('active');

    switchMainTab('matrix');
    showToast('🎉 研判长文与短视频矩阵资产已全部生成完毕！');
    refreshIcons();
}

// =========================================================================
// 7. 矩阵多平台切换 (微信 / 抖音 / 小红书)
// =========================================================================
function switchPlatform(platform) {
    currentActivePlatform = platform;

    // 更新胶囊按钮高亮
    document.getElementById('tabBtnWechat').classList.toggle('active', platform === 'wechat');
    document.getElementById('tabBtnDouyin').classList.toggle('active', platform === 'douyin');
    document.getElementById('tabBtnXiaohongshu').classList.toggle('active', platform === 'xiaohongshu');

    // 切换面板显示
    document.getElementById('paneWechat').classList.toggle('active', platform === 'wechat');
    document.getElementById('paneDouyin').classList.toggle('active', platform === 'douyin');
    document.getElementById('paneXiaohongshu').classList.toggle('active', platform === 'xiaohongshu');

    // 控制实时换肤工具条只在微信面板展示
    const quickBar = document.getElementById('themeQuickBar');
    if (quickBar) quickBar.style.display = platform === 'wechat' ? 'flex' : 'none';

    // 智能更新吸底操作按钮文本与行动
    const pubBtn = document.getElementById('mobilePublishBtn');
    const pubText = document.getElementById('mobilePubText');
    const pubIcon = document.getElementById('mobilePubIcon');

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
    refreshIcons();
}

function copyActiveContent() {
    let content = '';
    let name = '';
    if (currentActivePlatform === 'wechat') {
        const previewBox = document.getElementById('mobilePreviewContent');
        content = previewBox ? previewBox.innerText : '';
        name = '微信长文';
    } else if (currentActivePlatform === 'douyin') {
        content = document.getElementById('douyinScriptText').value;
        name = '抖音解说脚本';
    } else if (currentActivePlatform === 'xiaohongshu') {
        content = document.getElementById('xiaohongshuNoteText').value;
        name = '小红书笔记';
    }

    if (!content) {
        showToast('当前暂无可复制的内容', 'warning');
        return;
    }

    navigator.clipboard.writeText(content).then(() => {
        showToast(`已复制${name}到剪贴板！`);
    }).catch(() => {
        showToast('复制失败，请手动长按复制', 'error');
    });
}

// =========================================================================
// 8. 实时主题换肤与 AI 重绘配图
// =========================================================================
async function switchThemeQuick(themeKey, btnEl) {
    if (!currentGeneratedData || !currentGeneratedData.markdown_content) {
        showToast('请先生成文章后再进行主题换肤', 'warning');
        return;
    }

    document.querySelectorAll('.theme-chip').forEach(c => c.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    showToast('正在实时渲染微信内联样式...');

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
        showToast('换肤异常: ' + e.message, 'error');
    }
}

async function triggerRegenerateImage() {
    const styleSelect = document.getElementById('imageStyleSelect');
    const styleKey = styleSelect ? styleSelect.value : 'photojournalism';
    const title = currentGeneratedData ? currentGeneratedData.title : (document.getElementById('mobileTopicInput').value.trim() || '前沿战术推演');

    showToast('🎨 AI 正在按新风格重绘配图与封面...');
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

// =========================================================================
// 9. SQLite 历史智库文库管理 (Bottom Sheet)
// =========================================================================
async function loadHistoryArticles() {
    const container = document.getElementById('historyListContainer');
    if (!container) return;
    container.innerHTML = `
        <div class="sheet-loading-state">
            <i data-lucide="loader-2" class="spin-icon" style="width: 20px; height: 20px;"></i>
            <span>正在读取 SQLite 历史推文库...</span>
        </div>
    `;
    refreshIcons();

    try {
        const resp = await fetch('/api/articles/history');
        const data = await resp.json();
        if (data.code === 200 && data.articles && data.articles.length > 0) {
            renderHistoryCards(data.articles);
        } else {
            container.innerHTML = `
                <div class="sheet-loading-state">
                    <i data-lucide="archive" style="width: 28px; height: 28px; color: var(--text-light);"></i>
                    <span>文库暂无历史记录，去生成第一篇吧</span>
                </div>
            `;
            refreshIcons();
        }
    } catch (e) {
        container.innerHTML = `<div class="sheet-loading-state" style="color: #ef4444;">调阅失败: ${e.message}</div>`;
    }
}

function renderHistoryCards(articles) {
    const container = document.getElementById('historyListContainer');
    if (!container) return;

    let html = '';
    articles.forEach(art => {
        const isPublished = art.publish_status === 'published';
        const statusBadge = isPublished
            ? '<span style="color: #16a34a; font-weight: 600;">已推草稿箱</span>'
            : '<span style="color: #ca8a04; font-weight: 600;">草稿存档</span>';

        html += `
        <div class="history-card" onclick="loadHistoryArticleDetail(${art.id})">
            <div class="history-card-header">
                <span class="history-card-tag">${art.category || '深度研判'}</span>
                <span class="history-card-time">${art.created_at || ''}</span>
            </div>
            <div class="history-card-title">${art.title}</div>
            <div class="history-card-status">
                <i data-lucide="${isPublished ? 'check-circle' : 'file-edit'}" style="width: 12px; height: 12px; color: ${isPublished ? '#16a34a' : '#ca8a04'};"></i>
                <span>${statusBadge}</span>
                <span>·</span>
                <span>主题: ${art.theme || 'think_tank'}</span>
            </div>
        </div>
        `;
    });
    container.innerHTML = html;
    refreshIcons();
}

async function loadHistoryArticleDetail(id) {
    showToast('正在调阅 SQLite 历史档案...');
    closeBottomSheet('historySheet');

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

            const mockTitle = document.getElementById('previewMockTitle');
            if (mockTitle) mockTitle.innerText = art.title;

            const previewBox = document.getElementById('mobilePreviewContent');
            if (previewBox) previewBox.innerHTML = art.wechat_html;

            const douyinText = document.getElementById('douyinScriptText');
            if (douyinText) douyinText.value = art.douyin_script || '';

            const xhsText = document.getElementById('xiaohongshuNoteText');
            if (xhsText) xhsText.value = art.xiaohongshu_note || '';

            const statWord = document.getElementById('statWordCount');
            if (statWord) {
                const words = (art.markdown_content || '').length;
                statWord.innerText = `${words} 字 · 预计精读 ${Math.max(1, Math.round(words / 380))} 分钟`;
            }

            switchMainTab('matrix');
            showToast('已调阅历史推文：《' + art.title.substring(0, 16) + '...》');
        }
    } catch (e) {
        showToast('调阅失败: ' + e.message, 'error');
    }
}

// =========================================================================
// 10. 提示词配置管理 (Prompt Sheet)
// =========================================================================
async function loadPromptConfig() {
    try {
        const resp = await fetch('/api/prompts');
        const data = await resp.json();
        if (data.code === 200) {
            const sysEl = document.getElementById('cfgSystemPrompt');
            const userEl = document.getElementById('cfgUserPromptTemplate');
            if (sysEl) sysEl.value = data.system_prompt || '';
            if (userEl) userEl.value = data.user_prompt_template || '';
        }
    } catch (e) {
        console.error('拉取 Prompt 失败:', e);
    }
}

async function savePrompts() {
    const sysEl = document.getElementById('cfgSystemPrompt');
    const userEl = document.getElementById('cfgUserPromptTemplate');
    const sys = sysEl ? sysEl.value.trim() : '';
    const user = userEl ? userEl.value.trim() : '';

    if (!sys || !user) {
        showToast('提示词配置不能为空', 'warning');
        return;
    }

    try {
        const resp = await fetch('/api/prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ system_prompt: sys, user_prompt_template: user })
        });
        const res = await resp.json();
        if (res.code === 200) {
            showToast('✅ 智库 Prompt 配置已成功保存！');
            closeBottomSheet('promptSheet');
        } else {
            showToast('保存失败: ' + res.message, 'error');
        }
    } catch (e) {
        showToast('通信异常: ' + e.message, 'error');
    }
}

async function resetPrompts() {
    if (!confirm('确定要重置为 2026 官方预设 Prompt 吗？')) return;
    try {
        const resp = await fetch('/api/prompts/reset', { method: 'POST' });
        const res = await resp.json();
        if (res.code === 200) {
            const sysEl = document.getElementById('cfgSystemPrompt');
            const userEl = document.getElementById('cfgUserPromptTemplate');
            if (sysEl) sysEl.value = res.system_prompt || '';
            if (userEl) userEl.value = res.user_prompt_template || '';
            showToast('🔄 已恢复官方智库预设！');
        }
    } catch (e) {
        showToast('重置异常: ' + e.message, 'error');
    }
}

// =========================================================================
// 11. 微信公众平台草稿箱一键真实推送
// =========================================================================
async function triggerMobilePublish() {
    if (currentActivePlatform !== 'wechat') {
        copyActiveContent();
        return;
    }

    if (!currentGeneratedData || !currentGeneratedData.html_content) {
        showToast('暂无生成的微信图文，请先在「发现选题」执行生成', 'warning');
        return;
    }

    const pubBtn = document.getElementById('mobilePublishBtn');
    const pubSpinner = document.getElementById('mobilePubSpinner');
    const pubIcon = document.getElementById('mobilePubIcon');
    const pubText = document.getElementById('mobilePubText');

    pubBtn.disabled = true;
    if (pubSpinner) pubSpinner.style.display = 'block';
    if (pubIcon) pubIcon.style.display = 'none';
    if (pubText) pubText.innerText = '正在上传封面并推送到草稿箱...';

    try {
        const resp = await fetch('/api/publish', { method: 'POST' });
        const res = await resp.json();
        if (res.code === 200) {
            showToast('🎉 成功推送到微信公众平台草稿箱！');
            alert(`🎉 推送微信公众平台草稿箱成功！\n\n【草稿 Media ID】\n${res.media_id}\n\n请在手机「订阅号助手」App 中审核后一键群发！`);
        } else {
            showToast('推送失败: ' + res.message, 'error');
            alert('推送草稿箱失败: ' + res.message);
        }
    } catch (e) {
        showToast('推送异常: ' + e.message, 'error');
    } finally {
        pubBtn.disabled = false;
        if (pubSpinner) pubSpinner.style.display = 'none';
        if (pubIcon) pubIcon.style.display = 'inline-block';
        if (pubText) pubText.innerText = '一键推送到微信公众号草稿箱';
    }
}

// =========================================================================
// 12. 轻提示 (Toast)
// =========================================================================
let toastTimeout = null;
function showToast(msg, type = 'info') {
    const toast = document.getElementById('mobileToast');
    if (!toast) return;

    toast.innerText = msg;
    toast.classList.add('active');

    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('active');
    }, 2800);
}
