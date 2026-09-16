# -*- coding: utf-8 -*-
"""
微信公众号自动化发布系统 - 可视化 Web 控制台
职责：
提供现代化的浏览器可视化操作界面，支持：
1. 拖拽上传 PDF 智库报告 / 粘贴网页链接 / 输入热点主题；
2. 实时调用 DeepSeek-V3 写作 + Kolors 电影级生图 + 微信专属内联排版；
3. 右侧提供仿微信手机端的实时真实排版预览；
4. 点击「一键推送到微信草稿箱」按钮直接推送，并触发手机通知；
5. 查看微信草稿箱历史文章。
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>局势洞见 · 智库舆情与微信发布控制台</title>
    <style>
        :root {
            --bg-base: #0b0f19;
            --bg-card: rgba(18, 24, 38, 0.85);
            --border-color: rgba(255, 255, 255, 0.08);
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --accent: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            padding: 16px 32px;
            border-bottom: 1px solid var(--border-color);
            background: rgba(11, 15, 25, 0.8);
            backdrop-filter: blur(12px);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .badge {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 12px;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.4);
        }

        /* 手机移动端深度适配 */
        @media (max-width: 900px) {
            header { padding: 14px 18px; }
            main {
                grid-template-columns: 1fr;
                padding: 14px;
                gap: 16px;
            }
            .panel { padding: 18px 14px; }
            .preview-wrapper {
                padding: 14px 10px;
                width: 100%;
            }
            /* 手机端直接全宽展示正文，去掉多余的仿真手机外壳 */
            .phone-frame {
                width: 100% !important;
                height: auto !important;
                min-height: 500px;
                border: none !important;
                border-radius: 14px !important;
                box-shadow: none !important;
            }
            .phone-notch { display: none !important; }
            .btn {
                padding: 14px 20px;
                font-size: 15px;
            }
        }

        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            gap: 20px;
            height: fit-content;
        }

        .section-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* 拖拽上传区 */
        .dropzone {
            border: 2px dashed rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 28px 16px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(255, 255, 255, 0.02);
        }
        .dropzone:hover, .dropzone.dragover {
            border-color: var(--primary);
            background: rgba(59, 130, 246, 0.05);
        }

        input[type="text"], textarea {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 14px;
            color: var(--text-main);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        input[type="text"]:focus, textarea:focus {
            border-color: var(--primary);
        }

        .btn {
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        .btn:hover { background: var(--primary-hover); transform: translateY(-1px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-success { background: var(--accent); }
        .btn-success:hover { background: #059669; }

        /* 分类切换药丸标签 */
        .cat-pill {
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 14px;
            font-size: 11.5px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }
        .cat-pill:hover, .cat-pill.active {
            background: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            border-color: #3b82f6;
        }

        /* 右侧手机预览框 */
        .preview-wrapper {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 700px;
        }

        .phone-frame {
            width: 420px;
            height: 780px;
            border: 10px solid #1e293b;
            border-radius: 36px;
            background: #ffffff;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .phone-notch {
            height: 24px;
            background: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .notch-bar { width: 120px; height: 12px; background: #0f172a; border-radius: 0 0 8px 8px; }

        .phone-content {
            flex: 1;
            overflow-y: auto;
            background: #ffffff;
        }

        .empty-placeholder {
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #94a3b8;
            font-size: 14px;
            gap: 12px;
        }

        /* 加载动效 */
        .loader {
            display: none;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span>🛡️ 局势洞见</span>
            <span class="badge">自动化智库研判系统</span>
        </div>
        <div style="font-size: 13px; color: var(--text-muted);">
            微信公众平台草稿箱直连服务
        </div>
    </header>

    <main>
        <!-- 左侧操作配置面板 -->
        <div class="panel">
            <div class="section-title">📁 素材来源输入</div>

            <!-- PDF 拖拽上传 -->
            <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
                <div style="font-size: 32px; margin-bottom: 8px;">📄</div>
                <div style="font-weight: 500; font-size: 14px;" id="fileLabel">点击或拖拽智库 PDF 报告到此处</div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">支持 PDF / TXT / Markdown 格式报告</div>
                <input type="file" id="fileInput" style="display: none;" accept=".pdf,.txt,.md" onchange="handleFileSelect(this)">
            </div>

            <div style="text-align: center; color: var(--text-muted); font-size: 12px;">— 或者 —</div>

            <!-- 多源热点自动聚合探测模块 -->
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 12px; padding: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 13px; font-weight: 600; color: #60a5fa;">📡 多源防务热点探测池</span>
                    <button onclick="fetchHotTopics(currentCategory)" style="background: none; border: 1px solid rgba(96,165,250,0.4); color: #60a5fa; font-size: 11px; padding: 3px 8px; border-radius: 6px; cursor: pointer;">刷新源</button>
                </div>
                <!-- 多源分类切换标签 -->
                <div style="display: flex; gap: 6px; margin-bottom: 10px; overflow-x: auto; padding-bottom: 4px;">
                    <button class="cat-pill active" onclick="switchCategory('all', this)">🔥 全部</button>
                    <button class="cat-pill" onclick="switchCategory('middle_east', this)">🌊 红海/中东</button>
                    <button class="cat-pill" onclick="switchCategory('tech', this)">⚡ 硬核装备</button>
                    <button class="cat-pill" onclick="switchCategory('power', this)">🌐 大国博弈</button>
                </div>
                <div id="hotList" style="display: flex; flex-direction: column; gap: 8px; font-size: 12.5px; max-height: 280px; overflow-y: auto;">
                    <div style="color: var(--text-muted); text-align: center; padding: 12px;">正在加载多源防务数据...</div>
                </div>
            </div>

            <!-- 热点话题输入 -->
            <div>
                <label style="font-size: 13px; color: var(--text-muted); display: block; margin-bottom: 6px;">研判热点 / 新闻链接：</label>
                <input type="text" id="topicInput" placeholder="点击上方热点自动填入，或直接输入">
            </div>

            <!-- 生成按钮 -->
            <button class="btn" id="generateBtn" onclick="triggerGenerate()">
                <div class="loader" id="genLoader"></div>
                <span id="genBtnText">🚀 开始深度研判并生成图文</span>
            </button>

            <hr style="border: none; border-top: 1px solid var(--border-color);">

            <!-- 一键推送到微信按钮 -->
            <div class="section-title">📢 微信公众平台同步</div>
            <p style="font-size: 12.5px; color: var(--text-muted); line-height: 1.5;">
                文章生成满意后，点击下方按钮将图文、电影级大片封面及内嵌插图一键写入微信官方草稿箱，并触发手机通知。
            </p>
            <button class="btn btn-success" id="publishBtn" onclick="triggerPublish()" disabled>
                <div class="loader" id="pubLoader"></div>
                <span id="pubBtnText">📤 一键推送到微信草稿箱</span>
            </button>
            <div id="statusNotice" style="font-size: 13px; text-align: center; display: none;"></div>
        </div>

        <!-- 右侧手机端实时预览窗 -->
        <div class="preview-wrapper">
            <div style="font-size: 14px; font-weight: 600; color: var(--text-muted); margin-bottom: 16px;">
                📱 手机微信文章实时排版效果预览
            </div>
            <div class="phone-frame">
                <div class="phone-notch"><div class="notch-bar"></div></div>
                <div class="phone-content" id="phoneContent">
                    <div class="empty-placeholder">
                        <span style="font-size: 40px;">📰</span>
                        <span>等待生成... 生成后将在此呈现排版</span>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let selectedFile = null;
        let currentCategory = 'all';

        function switchCategory(cat, btn) {
            currentCategory = cat;
            document.querySelectorAll('.cat-pill').forEach(el => el.classList.remove('active'));
            btn.classList.add('active');
            fetchHotTopics(cat);
        }

        // 跨渠道多源抓取并展示防务热点
        async function fetchHotTopics(cat = 'all') {
            const listDiv = document.getElementById('hotList');
            listDiv.innerHTML = '<div style="color: #60a5fa; padding: 10px; text-align: center;">正在聚合多源防务流数据...</div>';
            try {
                const resp = await fetch(`/api/crawl?category=${cat}`);
                const data = await resp.json();
                if (data.code === 200 && data.topics.length) {
                    listDiv.innerHTML = '';
                    data.topics.forEach(t => {
                        const row = document.createElement('div');
                        row.style.padding = '10px 12px';
                        row.style.background = 'rgba(255,255,255,0.04)';
                        row.style.border = '1px solid rgba(255,255,255,0.06)';
                        row.style.borderRadius = '8px';
                        row.style.cursor = 'pointer';
                        row.style.transition = 'all 0.2s';
                        row.onmouseover = () => {
                            row.style.background = 'rgba(59,130,246,0.12)';
                            row.style.borderColor = '#3b82f6';
                        };
                        row.onmouseout = () => {
                            row.style.background = 'rgba(255,255,255,0.04)';
                            row.style.borderColor = 'rgba(255,255,255,0.06)';
                        };
                        row.onclick = () => {
                            document.getElementById('topicInput').value = t.title;
                            window.scrollTo({ top: document.getElementById('topicInput').offsetTop - 20, behavior: 'smooth' });
                        };
                        const srcBadge = t.source || '防务观察';
                        row.innerHTML = `
                            <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                                <span style="background: #1e3a8a; color: #93c5fd; padding: 1px 6px; border-radius: 4px; font-size: 10.5px;">#${t.keyword || '热点'}</span>
                                <span style="color: #64748b; font-size: 11px;">${srcBadge}</span>
                            </div>
                            <div style="font-weight:600; color:#f1f5f9; line-height:1.4;">${t.title}</div>
                            <div style="color: #94a3b8; font-size: 11.5px; margin-top: 4px; line-height: 1.4;">${t.summary || ''}</div>
                        `;
                        listDiv.appendChild(row);
                    });
                } else {
                    listDiv.innerHTML = '<div style="color: var(--text-muted); padding: 12px; text-align: center;">暂无该分类热点，可直接手动输入话题</div>';
                }
            } catch (err) {
                listDiv.innerHTML = '<div style="color: #ef4444; padding: 10px;">热点抓取异常: ' + err + '</div>';
            }
        }

        // 页面加载完毕后自动拉取一次热点
        window.addEventListener('DOMContentLoaded', () => {
            fetchHotTopics('all');
        });

        // 拖拽文件事件
        const dropzone = document.getElementById('dropzone');
        ['dragenter', 'dragover'].forEach(name => {
            dropzone.addEventListener(name, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
        });
        ['dragleave', 'drop'].forEach(name => {
            dropzone.addEventListener(name, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); });
        });
        dropzone.addEventListener('drop', (e) => {
            if (e.dataTransfer.files.length) {
                selectedFile = e.dataTransfer.files[0];
                document.getElementById('fileLabel').innerText = "已选择: " + selectedFile.name;
            }
        });

        function handleFileSelect(input) {
            if (input.files.length) {
                selectedFile = input.files[0];
                document.getElementById('fileLabel').innerText = "已选择: " + selectedFile.name;
            }
        }

        // 触发生成文章
        async function triggerGenerate() {
            const topic = document.getElementById('topicInput').value.trim();
            if (!selectedFile && !topic) {
                alert("请先选择 PDF 报告或输入研判热点！");
                return;
            }

            const genBtn = document.getElementById('generateBtn');
            const genLoader = document.getElementById('genLoader');
            const genBtnText = document.getElementById('genBtnText');
            const phoneContent = document.getElementById('phoneContent');

            genBtn.disabled = true;
            genLoader.style.display = "block";
            genBtnText.innerText = "正在深度改写与智能生图中 (约20秒)...";
            phoneContent.innerHTML = `<div class="empty-placeholder"><div class="loader" style="display:block; border-color: #3b82f6; border-top-color: transparent;"></div><span>正在调用 DeepSeek-V3 写作与 Kolors 生图中...</span></div>`;

            const formData = new FormData();
            if (selectedFile) {
                formData.append("file", selectedFile);
            }
            if (topic) {
                formData.append("topic", topic);
            }

            try {
                const resp = await fetch("/api/generate", {
                    method: "POST",
                    body: formData
                });
                const data = await resp.json();
                if (data.code === 200) {
                    phoneContent.innerHTML = data.html_content;
                    document.getElementById('publishBtn').disabled = false;
                    document.getElementById('statusNotice').style.display = "block";
                    document.getElementById('statusNotice').style.color = "#10b981";
                    document.getElementById('statusNotice').innerText = "✅ 文章排版与配图已生成就绪，请预览！";
                } else {
                    alert("生成失败: " + data.message);
                }
            } catch (err) {
                alert("网络请求失败: " + err);
            } finally {
                genBtn.disabled = false;
                genLoader.style.display = "none";
                genBtnText.innerText = "🚀 开始深度研判并生成图文";
            }
        }

        // 触发推送到微信草稿箱
        async function triggerPublish() {
            const pubBtn = document.getElementById('publishBtn');
            const pubLoader = document.getElementById('pubLoader');
            const pubBtnText = document.getElementById('pubBtnText');
            const notice = document.getElementById('statusNotice');

            pubBtn.disabled = true;
            pubLoader.style.display = "block";
            pubBtnText.innerText = "正在推送到微信草稿箱...";

            try {
                const resp = await fetch("/api/publish", { method: "POST" });
                const data = await resp.json();
                if (data.code === 200) {
                    notice.style.display = "block";
                    notice.style.color = "#10b981";
                    notice.innerHTML = `🎉 成功录入草稿箱！Draft ID: <code>${data.draft_media_id}</code><br>手机微信已收到推送通知，请在「订阅号助手」一键群发！`;
                } else {
                    notice.style.display = "block";
                    notice.style.color = "#ef4444";
                    notice.innerText = "推送失败: " + data.message;
                }
            } catch (err) {
                alert("网络请求失败: " + err);
            } finally {
                pubBtn.disabled = false;
                pubLoader.style.display = "none";
                pubBtnText.innerText = "📤 一键推送到微信草稿箱";
            }
        }
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
            # 抓取最新防务热点列表（支持分类查询）
            query_params = parse_qs(urlparse(self.path).query)
            cat = query_params.get("category", ["all"])[0]
            topics = DefenseCrawler.fetch_multi_source_topics(category=cat, limit=6)
            self.send_json_response(200, "获取热点成功", {"topics": topics})
        elif url_path.startswith("/assets/"):
            # 返回静态资源（图片等）
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
        """处理文章与配图生成请求"""
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
            # 保存到临时文件
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

        # 调用 AI 深度撰写
        writer = AIWriter()
        try:
            article_data = writer.generate_article(raw_content, user_focus=topic or "")
        except Exception as e:
            self.send_json_response(500, f"AI 写作失败: {e}")
            return

        title = article_data.get("title", "局势观察特稿")
        digest = article_data.get("digest", "")
        markdown_content = article_data.get("markdown_content", "")

        # 基础排版
        html_content = WeChatFormatter.format_markdown_to_wechat_html(
            markdown_content,
            author=settings.WECHAT_DEFAULT_AUTHOR
        )

        # 尝试调用 Kolors 电影级生图
        ai_img = ImageService.generate_ai_flux_image(
            prompt="红海曼德海峡，一艘灰色现代化军舰在海面航行，纪实摄影风格，冷色调，高清大片"
        )
        if ai_img and Path(ai_img).exists():
            candidate_illustrations.append(ai_img)
        elif not candidate_illustrations:
            tactical = ImageService.generate_tactical_infographic(title)
            if tactical:
                candidate_illustrations.append(tactical)

        # 将本地图片以可访问的 Web 链接形式插入预览
        if candidate_illustrations:
            first_img = candidate_illustrations[0]
            # Web 相对访问路径
            rel_url = f"/assets/{Path(first_img).name}"
            html_content = ImageService.insert_illustration_to_html(
                html_content=html_content,
                image_cdn_url=rel_url,
                caption="▲ 关键战术态势与地理空间研判示意",
                insert_after_part="PART 01"
            )

        # 生成 2.35:1 封面
        cover_path = CoverGenerator.generate_default_cover(
            title,
            source_photo=candidate_illustrations[0] if candidate_illustrations else None
        )

        # 存入全局缓存
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
        """处理推送到微信公众号草稿箱请求"""
        if not CURRENT_CACHE["title"] or not CURRENT_CACHE["html_content"]:
            self.send_json_response(400, "尚未生成任何文章，请先点击生成！")
            return

        wechat = WeChatClient()

        # 上传插图到微信 CDN 并替换本地 Web 链接为微信官方永久 CDN 链接
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

        # 上传封面素材
        try:
            thumb_id = wechat.upload_thumb_material(CURRENT_CACHE["cover_image"])
        except Exception as e:
            self.send_json_response(500, f"上传封面素材失败: {e}")
            return

        # 写入草稿箱
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

        # 触发手机通知
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
    logger.info(f"🌐 局势洞见 Web 可视化控制台已就绪！")
    logger.info(f"👉 访问地址: http://localhost:{PORT}")
    logger.info(f"👉 部署到云服务器后访问: http://<云服务器公网IP>:{PORT}")
    logger.info("==================================================")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
