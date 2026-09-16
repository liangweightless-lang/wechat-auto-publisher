/**
 * 局势洞见 · 移动端交互与 API 客户端 (App-Ready Client)
 * 职责：
 * 1. 管理选定材料与活动战区状态；
 * 2. 调度服务端 REST API (/api/topics, /api/generate, /api/publish)；
 * 3. 驱动微信推文仿真阅读器渲染与富文本一键复制；
 * 4. 支持浅色/深色主题持久化切换。
 */

let mobileSelectedFile = null;
let activeCategory = 'all';

// 主题切换
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const target = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', target);
    document.getElementById('themeIcon').innerText = target === 'dark' ? '🌙' : '☀️';
    localStorage.setItem('wechat_theme', target);
}

// 初始化主题偏好
(function initTheme() {
    const saved = localStorage.getItem('wechat_theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    window.addEventListener('DOMContentLoaded', () => {
        const icon = document.getElementById('themeIcon');
        if (icon) icon.innerText = saved === 'dark' ? '🌙' : '☀️';
    });
})();

// 屏幕居中 Toast 消息
function showToast(msg, isError = false) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.style.background = isError ? "#ef4444" : "#0f172a";
    t.style.display = "block";
    setTimeout(() => { t.style.display = "none"; }, 3000);
}

// 视图切换 (选题编辑 / 仿真实机预览)
function switchView(viewName) {
    document.querySelectorAll('.view-pane').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.segment-btn').forEach(el => el.classList.remove('active'));

    if (viewName === 'edit') {
        document.getElementById('viewEdit').classList.add('active');
        document.getElementById('tabNavEdit').classList.add('active');
    } else {
        document.getElementById('viewPreview').classList.add('active');
        document.getElementById('tabNavPreview').classList.add('active');
        document.getElementById('previewDot').style.display = 'none';
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 处理上传报告文件
function handleMobileFile(input) {
    if (input.files.length) {
        mobileSelectedFile = input.files[0];
        const label = document.getElementById('mobileFileLabel');
        label.innerText = "已就绪: " + mobileSelectedFile.name;
        label.style.color = "var(--primary)";
        showToast("已成功选定报告文件！");
    }
}

// 战区分类切换
function selectCategory(cat, el) {
    activeCategory = cat;
    document.querySelectorAll('.tab-chip').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    fetchHotTopics(cat);
}

// 拉取热点列表 (GET /api/topics)
async function fetchHotTopics(cat = 'all') {
    const list = document.getElementById('mobileHotList');
    list.innerHTML = '<div style="text-align: center; padding: 24px; font-size: 13px; color: var(--text-muted);">正在拉取最新防务情报...</div>';
    try {
        const resp = await fetch(`/api/topics?category=${cat}`);
        const data = await resp.json();
        if (data.code === 200 && data.topics.length) {
            list.innerHTML = '';
            data.topics.forEach((t, idx) => {
                const item = document.createElement('div');
                item.className = 'topic-row-item';
                item.onclick = () => {
                    const inp = document.getElementById('mobileTopicInput');
                    inp.value = t.title;
                    autoResizeTextarea(inp);
                    showToast("已选定话题！");
                    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                };
                const rankNum = (idx + 1) < 10 ? '0' + (idx + 1) : (idx + 1);
                item.innerHTML = `
                    <div class="topic-rank-num">${rankNum}</div>
                    <div class="topic-main-content">
                        <div class="topic-top-meta">
                            <span class="topic-badge-tag">${t.level || t.keyword || '焦点'}</span>
                            <span class="topic-origin">${t.source || '防务通报'}</span>
                        </div>
                        <div class="topic-headline">${t.title}</div>
                        <div class="topic-abstract">${t.summary || ''}</div>
                    </div>
                `;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 24px; font-size: 12px;">暂无该分类动态，可直接输入研究话题</div>';
        }
    } catch (e) {
        list.innerHTML = '<div style="color: #ef4444; padding: 16px; font-size: 12px;">网络拉取异常: ' + e + '</div>';
    }
}

// 步骤弹窗动画
function updateStep(stepNum) {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById('step' + i);
        el.classList.remove('active', 'done');
        if (i < stepNum) {
            el.classList.add('done');
            el.querySelector('.step-circle').innerText = '✓';
        } else if (i === stepNum) {
            el.classList.add('active');
            el.querySelector('.step-circle').innerText = i;
        } else {
            el.querySelector('.step-circle').innerText = i;
        }
    }
}

// 输入框自适应高度
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.max(72, Math.min(textarea.scrollHeight, 200)) + 'px';
    const len = textarea.value.trim().length;
    const countEl = document.getElementById('charCount');
    if (countEl) countEl.innerText = len + ' 字';
}

// 清空输入框
function clearTopicInput() {
    const input = document.getElementById('mobileTopicInput');
    input.value = '';
    autoResizeTextarea(input);
    showToast("已清空输入框");
}

// 核心生成流程 (POST /api/generate)
async function triggerMobileGenerate() {
    const topic = document.getElementById('mobileTopicInput').value.trim();
    if (!mobileSelectedFile && !topic) {
        showToast("⚠️ 请先点选上方话题或选择报告！", true);
        const inputEl = document.getElementById('mobileTopicInput');
        if (inputEl) { inputEl.focus(); }
        return;
    }

    const modal = document.getElementById('progressModal');
    modal.classList.add('active');
    updateStep(1);

    const timer1 = setTimeout(() => updateStep(2), 3500);
    const timer2 = setTimeout(() => updateStep(3), 8500);
    const timer3 = setTimeout(() => updateStep(4), 16000);
    const timer4 = setTimeout(() => updateStep(5), 23000);

    const formData = new FormData();
    if (mobileSelectedFile) formData.append("file", mobileSelectedFile);
    if (topic) formData.append("topic", topic);

    try {
        const resp = await fetch("/api/generate", { method: "POST", body: formData });
        const data = await resp.json();
        clearTimeout(timer1); clearTimeout(timer2); clearTimeout(timer3); clearTimeout(timer4);
        modal.classList.remove('active');

        if (data.code === 200) {
            document.getElementById('mobilePreviewContent').innerHTML = data.html_content;
            document.getElementById('previewMockTitle').innerText = data.title;
            document.getElementById('previewDot').style.display = 'block';

            const words = data.word_count || Math.round(data.html_content.length / 2);
            document.getElementById('statWordCount').innerText = `${words.toLocaleString()} 字 · 约 ${Math.ceil(words / 400)} 分钟`;

            showToast("🎉 推文排版与大片配图已就绪！");
            setTimeout(() => { switchView('preview'); }, 400);
        } else {
            showToast("生成失败: " + data.message, true);
        }
    } catch (err) {
        clearTimeout(timer1); clearTimeout(timer2); clearTimeout(timer3); clearTimeout(timer4);
        modal.classList.remove('active');
        showToast("网络连接异常: " + err, true);
    }
}

// 一键复制微信富文本排版
function copyWechatHtml() {
    const content = document.getElementById('mobilePreviewContent');
    if (!content || content.innerText.includes('暂无生成内容')) {
        showToast("暂无可复制的内容", true);
        return;
    }

    try {
        const blob = new Blob([content.innerHTML], { type: 'text/html' });
        const textBlob = new Blob([content.innerText], { type: 'text/plain' });
        const item = new ClipboardItem({
            'text/html': blob,
            'text/plain': textBlob
        });
        navigator.clipboard.write([item]).then(() => {
            showToast("📋 微信富文本已复制！可以直接在手机微信粘贴。");
        }).catch(() => {
            navigator.clipboard.writeText(content.innerText);
            showToast("已复制纯文本格式内容");
        });
    } catch (e) {
        showToast("复制失败，请长按文本复制", true);
    }
}

// 一键推送到微信草稿箱 (POST /api/publish)
async function triggerMobilePublish() {
    const previewContent = document.getElementById('mobilePreviewContent');
    if (!previewContent || previewContent.innerText.includes('暂无生成内容')) {
        showToast("⚠️ 请先在【选题与生成】中点击生成文章，再推送到草稿箱！", true);
        switchView('edit');
        return;
    }

    const btn = document.getElementById('mobilePublishBtn');
    const spinner = document.getElementById('mobilePubSpinner');
    const text = document.getElementById('mobilePubText');

    btn.disabled = true;
    spinner.style.display = "inline-block";
    text.innerText = "正在推送到微信公众号草稿箱...";

    try {
        const resp = await fetch("/api/publish", { method: "POST" });
        const data = await resp.json();
        if (data.code === 200) {
            showToast("🚀 成功推送到微信草稿箱！手机已收到推送提醒。");
        } else {
            showToast("推送草稿箱失败: " + data.message, true);
        }
    } catch (err) {
        showToast("网络通信异常: " + err, true);
    } finally {
        btn.disabled = false;
        spinner.style.display = "none";
        text.innerText = "📤 一键推送到微信公众号草稿箱";
    }
}

// 页面加载完毕初始化热搜情报榜
window.addEventListener('DOMContentLoaded', () => {
    fetchHotTopics('all');
});
