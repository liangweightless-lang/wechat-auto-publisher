# -*- coding: utf-8 -*-
"""
微信公众号自动化发布系统 - 移动端专属可视化 Web 控制台 (Mobile-First)
职责：
1. 专为手机端交互深度定制（仿微信原生小程序/App交互质感）；
2. 手机端大卡片一键上传微信/手机中的 PDF 智库报告；
3. 热点关键词横向滑动胶囊与单指点选；
4. 生成后自动无缝滑入「微信真实排版全屏预览」；
5. 手机屏幕底部常驻「一键推送到微信草稿箱」吸底快捷按钮。
"""

import os
import json
import cgi
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from config.settings import settings, logger
from core import WeChatClient, ContentParser, AIWriter, WeChatFormatter, CoverGenerator, ImageService, DefenseCrawler
from notify import Notifier

PORT = 8080
BASE_DIR = Path(__file__).resolve().parent

# 临时内存缓存上一次生成的内容，供一键推送
CURRENT_CACHE = {
    "title": "",
    "digest": "",
    "html_content": "",
    "cover_image": "",
    "thumb_media_id": ""
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>局势洞见 · 手机发布工作台</title>
    <style>
        :root {
            --bg-base: #0f172a;
            --bg-surface: #1e293b;
            --border-color: #334155;
            --primary: #3b82f6;
            --primary-active: #1d4ed8;
            --wechat-green: #07c160;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding-bottom: calc(75px + env(safe-area-inset-bottom));
        }

        /* 顶部导航栏 */
        .app-header {
            position: sticky;
            top: 0;
            z-index: 50;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .app-title {
            font-size: 17px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-pill {
            font-size: 11px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            padding: 2px 8px;
            border-radius: 10px;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* 手机端 Tab 切换栏 */
        .tab-bar {
            display: flex;
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 50px;
            z-index: 40;
        }
        .tab-item {
            flex: 1;
            text-align: center;
            padding: 12px 0;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            position: relative;
            transition: all 0.2s;
        }
        .tab-item.active {
            color: #60a5fa;
        }
        .tab-item.active::after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 20%;
            width: 60%;
            height: 3px;
            background: #3b82f6;
            border-radius: 3px 3px 0 0;
        }

        /* 视图容器 */
        .view-section { display: none; padding: 16px; max-width: 680px; margin: 0 auto; width: 100%; }
        .view-section.active { display: block; }

        /* 手机端卡片式容器 */
        .card {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
        }
        .card-header {
            font-size: 14px;
            font-weight: 600;
            color: #93c5fd;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* 手机专属文件选择器 */
        .mobile-upload-btn {
            background: rgba(59, 130, 246, 0.08);
            border: 1.5px dashed #3b82f6;
            border-radius: 12px;
            padding: 20px 14px;
            text-align: center;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .mobile-upload-btn:active { background: rgba(59, 130, 246, 0.18); }

        /* 移动端横向滑动标签 */
        .pill-scroll {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 6px;
            margin-bottom: 10px;
            scrollbar-width: none;
        }
        .pill-scroll::-webkit-scrollbar { display: none; }
        .cat-chip {
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .cat-chip.active {
            background: #2563eb;
            color: #ffffff;
            border-color: #3b82f6;
        }

        /* 热点列表 */
        .topic-item {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
            cursor: pointer;
        }
        .topic-item:active { background: rgba(59, 130, 246, 0.2); }

        /* 输入框 */
        .input-box {
            width: 100%;
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 14px;
            color: #ffffff;
            font-size: 14px;
            outline: none;
            margin-bottom: 12px;
        }
        .input-box:focus { border-color: var(--primary); }

        /* 大操作按钮 */
        .action-btn {
            width: 100%;
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 15px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .action-btn:active { background: var(--primary-active); }

        /* 手机端微信文章全宽预览页面 */
        .preview-container {
            background: #ffffff;
            border-radius: 12px;
            padding: 16px;
            min-height: 500px;
            color: #2d3748;
        }

        /* 底部常驻吸底条 */
        .bottom-action-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(15, 23, 42, 0.96);
            backdrop-filter: blur(16px);
            border-top: 1px solid var(--border-color);
            padding: 10px 16px calc(10px + env(safe-area-inset-bottom)) 16px;
            display: flex;
            gap: 12px;
        }
        .btn-wechat-push {
            flex: 1;
            background: var(--wechat-green);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 13px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            box-shadow: 0 4px 14px rgba(7, 193, 96, 0.35);
        }
        .btn-wechat-push:disabled { opacity: 0.4; cursor: not-allowed; box-shadow: none; }
        .btn-wechat-push:active { background: #06ad56; }

        /* 动效 */
        .spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
            display: none;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Toast 气泡提示 */
        #toast {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 200;
            background: rgba(16, 185, 129, 0.95);
            color: #fff;
            padding: 12px 22px;
            border-radius: 24px;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            display: none;
            backdrop-filter: blur(8px);
        }
    </style>
</head>
<body>

    <!-- 顶部状态栏 -->
    <header class="app-header">
        <div class="app-title">
            <span>🛡️ 局势洞见</span>
            <span class="status-pill">● 在线</span>
        </div>
        <div style="font-size: 12px; color: var(--text-muted);">
            微信草稿箱协同
        </div>
    </header>

    <!-- 手机端顶部 Tab 切换 -->
    <div class="tab-bar">
        <div class="tab-item active" id="tabNavEdit" onclick="switchView('edit')">
            ✍️ 选题与生成
        </div>
        <div class="tab-item" id="tabNavPreview" onclick="switchView('preview')">
            📱 微信效果预览 <span id="previewDot" style="display:none; color: #10b981;">●</span>
        </div>
    </div>

    <!-- 视图 1：选题与配置 -->
    <div class="view-section active" id="viewEdit">
        
        <!-- 方式 A：文件快速导入 -->
        <div class="card">
            <div class="card-header">
                <span>📁 智库报告一键导入</span>
                <span style="font-size: 11px; color: var(--text-muted);">PDF / 文本</span>
            </div>
            <div class="mobile-upload-btn" onclick="document.getElementById('mobileFileInput').click()">
                <div style="font-size: 28px;">📄</div>
                <div style="font-size: 14px; font-weight: 600;" id="mobileFileLabel">点击从手机中选择 PDF 报告</div>
                <div style="font-size: 11px; color: var(--text-muted);">支持微信传过来的《舆情报告》直接上传</div>
                <input type="file" id="mobileFileInput" style="display: none;" accept=".pdf,.txt,.md" onchange="handleMobileFile(this)">
            </div>
        </div>

        <!-- 方式 B：热点多源雷达 -->
        <div class="card">
            <div class="card-header">
                <span>📡 实时防务热点探测池</span>
                <span onclick="fetchHotTopics(activeCategory)" style="font-size: 12px; color: #60a5fa; cursor: pointer;">🔄 刷新源</span>
            </div>
            <!-- 横向滚动胶囊分类 -->
            <div class="pill-scroll">
                <div class="cat-chip active" onclick="selectCategory('all', this)">🔥 全部热点</div>
                <div class="cat-chip" onclick="selectCategory('middle_east', this)">🌊 红海/中东</div>
                <div class="cat-chip" onclick="selectCategory('tech', this)">⚡ 硬核装备</div>
                <div class="cat-chip" onclick="selectCategory('power', this)">🌐 大国博弈</div>
            </div>
            <div id="mobileHotList">
                <div style="color: var(--text-muted); text-align: center; padding: 14px; font-size: 12px;">正在连接防务情报流...</div>
            </div>
        </div>

        <!-- 焦点输入与执行 -->
        <div class="card">
            <div class="card-header">
                <span>🎯 当前研判焦点主题</span>
            </div>
            <input type="text" class="input-box" id="mobileTopicInput" placeholder="点击上方热点自动填入，或直接输入">
            <button class="action-btn" id="mobileGenBtn" onclick="triggerMobileGenerate()">
                <div class="spinner" id="mobileGenSpinner"></div>
                <span id="mobileGenText">🚀 开始深度撰写并配图 (约20秒)</span>
            </button>
        </div>
    </div>

    <!-- 视图 2：微信原生排版预览 -->
    <div class="view-section" id="viewPreview">
        <div class="preview-container" id="mobilePreviewContent">
            <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
                <div style="font-size: 40px; margin-bottom: 12px;">📰</div>
                <div style="font-weight: 600; font-size: 15px;">暂无生成内容</div>
                <div style="font-size: 12px; margin-top: 6px;">请在「选题与生成」页面选择报告或热点后点击生成</div>
            </div>
        </div>
    </div>

    <!-- 手机底部常驻操作栏 -->
    <div class="bottom-action-bar">
        <button class="btn-wechat-push" id="mobilePublishBtn" onclick="triggerMobilePublish()" disabled>
            <div class="spinner" id="mobilePubSpinner"></div>
            <span id="mobilePubText">📤 一键推送到微信公众号草稿箱</span>
        </button>
    </div>

    <!-- 气泡提示 -->
    <div id="toast"></div>

    <script>
        let mobileSelectedFile = null;
        let activeCategory = 'all';

        function showToast(msg, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.background = isError ? "rgba(239, 68, 68, 0.95)" : "rgba(16, 185, 129, 0.95)";
            t.style.display = "block";
            setTimeout(() => { t.style.display = "none"; }, 3500);
        }

        function switchView(viewName) {
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-item').forEach(el => el.classList.remove('active'));

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

        function handleMobileFile(input) {
            if (input.files.length) {
                mobileSelectedFile = input.files[0];
                document.getElementById('mobileFileLabel').innerText = "已选: " + mobileSelectedFile.name;
                document.getElementById('mobileFileLabel').style.color = "#60a5fa";
            }
        }

        function selectCategory(cat, el) {
            activeCategory = cat;
            document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            fetchHotTopics(cat);
        }

        async function fetchHotTopics(cat = 'all') {
            const list = document.getElementById('mobileHotList');
            list.innerHTML = '<div style="color: #60a5fa; text-align: center; padding: 12px; font-size: 12px;">正在探测最新防务流...</div>';
            try {
                const resp = await fetch(`/api/crawl?category=${cat}`);
                const data = await resp.json();
                if (data.code === 200 && data.topics.length) {
                    list.innerHTML = '';
                    data.topics.forEach(t => {
                        const item = document.createElement('div');
                        item.className = 'topic-item';
                        item.onclick = () => {
                            document.getElementById('mobileTopicInput').value = t.title;
                            showToast("已自动填入话题！");
                        };
                        item.innerHTML = `
                            <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                                <span style="background: #1e3a8a; color: #93c5fd; padding: 1px 6px; border-radius: 4px; font-size: 10px;">#${t.keyword || '焦点'}</span>
                                <span style="color: #64748b; font-size: 11px;">${t.source || '智库态势'}</span>
                            </div>
                            <div style="font-size: 13.5px; font-weight: 600; color: #f1f5f9; line-height: 1.4;">${t.title}</div>
                        `;
                        list.appendChild(item);
                    });
                } else {
                    list.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 12px; font-size: 12px;">暂无该分类选题，可手动输入</div>';
                }
            } catch (e) {
                list.innerHTML = '<div style="color: #ef4444; padding: 10px; font-size: 12px;">拉取异常: ' + e + '</div>';
            }
        }

        async function triggerMobileGenerate() {
            const topic = document.getElementById('mobileTopicInput').value.trim();
            if (!mobileSelectedFile && !topic) {
                alert("请先选择 PDF 报告文件或输入研判热点！");
                return;
            }

            const btn = document.getElementById('mobileGenBtn');
            const spinner = document.getElementById('mobileGenSpinner');
            const text = document.getElementById('mobileGenText');

            btn.disabled = true;
            spinner.style.display = "inline-block";
            text.innerText = "深度改写与大片配图中 (约20秒)...";

            const formData = new FormData();
            if (mobileSelectedFile) formData.append("file", mobileSelectedFile);
            if (topic) formData.append("topic", topic);

            try {
                const resp = await fetch("/api/generate", { method: "POST", body: formData });
                const data = await resp.json();
                if (data.code === 200) {
                    document.getElementById('mobilePreviewContent').innerHTML = data.html_content;
                    document.getElementById('mobilePublishBtn').disabled = false;
                    document.getElementById('previewDot').style.display = 'inline';
                    showToast("🎉 图文排版与配图已生成就绪！");
                    // 自动滑向预览页
                    setTimeout(() => { switchView('preview'); }, 600);
                } else {
                    alert("生成失败: " + data.message);
                }
            } catch (err) {
                alert("网络请求异常: " + err);
            } finally {
                btn.disabled = false;
                spinner.style.display = "none";
                text.innerText = "🚀 开始深度撰写并配图 (约20秒)";
            }
        }

        async function triggerMobilePublish() {
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
                    showToast("🎉 成功录入草稿箱！手机微信已收到通知");
                    alert("🎉 恭喜！文章已成功进入微信公众号草稿箱！\\n\\n请打开手机「订阅号助手」App，即可一键群发！");
                } else {
                    showToast("推送失败: " + data.message, true);
                    alert("推送失败: " + data.message);
                }
            } catch (e) {
                alert("网络异常: " + e);
            } finally {
                btn.disabled = false;
                spinner.style.display = "none";
                text.innerText = "📤 一键推送到微信公众号草稿箱";
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            fetchHotTopics('all');
        });
    </script>
</body>
</html>
"""


class WebRequestHandler(SimpleHTTPRequestHandler):
    """可视化控制台 HTTP 请求处理器"""

    def do_GET(self):
        url_path = urlparse(self.path).path
        if url_path == "/" or url_path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif url_path == "/api/crawl":
            query_params = parse_qs(urlparse(self.path).query)
            cat = query_params.get("category", ["all"])[0]
            topics = DefenseCrawler.fetch_multi_source_topics(category=cat, limit=6)
            self.send_json_response(200, "获取热点成功", {"topics": topics})
        elif url_path.startswith("/assets/"):
            file_path = BASE_DIR / url_path.lstrip("/")
            if file_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        url_path = urlparse(self.path).path
        if url_path == "/api/generate":
            self.handle_generate()
        elif url_path == "/api/publish":
            self.handle_publish()
        else:
            self.send_error(404)

    def handle_generate(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_json_response(400, "必须使用 multipart/form-data")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers["Content-Type"]}
        )

        topic = form.getvalue("topic", "")
        raw_content = ""
        candidate_illustrations = []

        if "file" in form and form["file"].filename:
            file_item = form["file"]
            file_bytes = file_item.file.read()
            upload_dir = BASE_DIR / "assets" / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            saved_file = upload_dir / file_item.filename
            with open(saved_file, "wb") as f:
                f.write(file_bytes)

            if saved_file.suffix.lower() == ".pdf":
                raw_content = ContentParser.extract_from_pdf(str(saved_file))
                candidate_illustrations = ImageService.extract_images_from_pdf(str(saved_file))
            else:
                raw_content = ContentParser.extract_from_text_file(str(saved_file))
        elif topic:
            if topic.startswith("http://") or topic.startswith("https://"):
                raw_content = ContentParser.extract_from_url(topic)
                candidate_illustrations = ImageService.extract_images_from_url(topic)
            else:
                raw_content = f"请围绕当前焦点话题进行深度智库研判：{topic}"

        if not raw_content or len(raw_content.strip()) < 20:
            self.send_json_response(400, "未能提取到有效素材文本")
            return

        writer = AIWriter()
        try:
            article_data = writer.generate_article(raw_content, user_focus=topic or "")
        except Exception as e:
            self.send_json_response(500, f"AI 写作失败: {e}")
            return

        title = article_data.get("title", "局势观察特稿")
        digest = article_data.get("digest", "")
        markdown_content = article_data.get("markdown_content", "")

        html_content = WeChatFormatter.format_markdown_to_wechat_html(
            markdown_content,
            author=settings.WECHAT_DEFAULT_AUTHOR
        )

        ai_img = ImageService.generate_ai_flux_image(
            prompt="红海曼德海峡，一艘灰色现代化军舰在海面航行，纪实摄影风格，冷色调，高清大片"
        )
        if ai_img and Path(ai_img).exists():
            candidate_illustrations.append(ai_img)
        elif not candidate_illustrations:
            tactical = ImageService.generate_tactical_infographic(title)
            if tactical:
                candidate_illustrations.append(tactical)

        if candidate_illustrations:
            first_img = candidate_illustrations[0]
            rel_url = f"/assets/{Path(first_img).name}"
            html_content = ImageService.insert_illustration_to_html(
                html_content=html_content,
                image_cdn_url=rel_url,
                caption="▲ 关键战术态势与地理空间研判示意",
                insert_after_part="PART 01"
            )

        cover_path = CoverGenerator.generate_default_cover(
            title,
            source_photo=candidate_illustrations[0] if candidate_illustrations else None
        )

        CURRENT_CACHE["title"] = title
        CURRENT_CACHE["digest"] = digest
        CURRENT_CACHE["html_content"] = html_content
        CURRENT_CACHE["cover_image"] = cover_path
        CURRENT_CACHE["candidate_illustrations"] = candidate_illustrations

        self.send_json_response(200, "生成成功", {
            "title": title,
            "digest": digest,
            "html_content": html_content
        })

    def handle_publish(self):
        if not CURRENT_CACHE["title"] or not CURRENT_CACHE["html_content"]:
            self.send_json_response(400, "尚未生成任何文章，请先点击生成！")
            return

        wechat = WeChatClient()
        final_html = CURRENT_CACHE["html_content"]
        candidates = CURRENT_CACHE.get("candidate_illustrations", [])
        if candidates:
            for img_p in candidates[:2]:
                try:
                    cdn_url = wechat.upload_content_image(img_p)
                    rel_url = f"/assets/{Path(img_p).name}"
                    final_html = final_html.replace(rel_url, cdn_url)
                except Exception as e:
                    logger.warning(f"上传插图到微信 CDN 失败: {e}")

        try:
            thumb_id = wechat.upload_thumb_material(CURRENT_CACHE["cover_image"])
        except Exception as e:
            self.send_json_response(500, f"上传封面素材失败: {e}")
            return

        try:
            draft_id = wechat.create_draft(
                title=CURRENT_CACHE["title"],
                content_html=final_html,
                thumb_media_id=thumb_id,
                digest=CURRENT_CACHE["digest"]
            )
        except Exception as e:
            self.send_json_response(500, f"写入草稿箱失败: {e}")
            return

        Notifier.notify_publish_success(CURRENT_CACHE["title"], CURRENT_CACHE["digest"], draft_id)

        self.send_json_response(200, "发布草稿成功", {
            "draft_media_id": draft_id
        })

    def send_json_response(self, code: int, message: str, data: dict = None):
        self.send_response(200 if code == 200 else code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        res = {"code": code, "message": message}
        if data:
            res.update(data)
        self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, WebRequestHandler)
    logger.info("==================================================")
    logger.info(f"🌐 局势洞见 移动端专属 Web 控制台已启动！")
    logger.info(f"👉 访问地址: http://localhost:{PORT}")
    logger.info(f"👉 手机/电脑公网访问: http://<云服务器IP>:{PORT}")
    logger.info("==================================================")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
