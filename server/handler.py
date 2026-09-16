from typing import Any, Dict, Optional
# -*- coding: utf-8 -*-
"""
局势洞见 · RESTful API 与静态服务路由分发器 (App-Ready Backend)
设计原则：
1. 模块化解耦：纯 JSON REST API，可直接供 Web 端、原生 App 或微信小程序无缝调用；
2. 静态资源托管：映射 /static/* 静态资源目录；
3. 业务下沉：所有 AI 写作、爬虫、微信 API 与排版均下沉至 core 模块。
"""

import os
import json
import cgi
import mimetypes
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from config.settings import settings, logger
from core import WeChatClient, ContentParser, AIWriter, WeChatFormatter, CoverGenerator, ImageService, DefenseCrawler
from notify import Notifier

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# 临时内存缓存上一次生成的内容
CURRENT_CACHE = {
    "title": "",
    "digest": "",
    "html_content": "",
    "markdown_content": "",
    "cover_image": "",
    "thumb_media_id": "",
    "word_count": 0,
    "read_time": 0
}


class AppAPIHandler(SimpleHTTPRequestHandler):
    """模块化 RESTful API 与静态资源分发器"""

    def _send_json(self, data: dict, code: int = 200):
        """统一发送 JSON 响应格式"""
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        """处理 CORS 预检请求（供移动 App 跨域调用）"""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. 首页静态页面重定向
        if path == "/" or path == "/index.html":
            self._serve_static_file(STATIC_DIR / "index.html")
            return

        # 2. /static/ 静态文件托管
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            target_file = STATIC_DIR / rel_path
            if target_file.exists() and target_file.is_file():
                self._serve_static_file(target_file)
                return
            self.send_error(404, "Static File Not Found")
            return

        # 3. [API] 探测情报与战报列表: GET /api/topics 或 GET /api/crawl
        if path in ["/api/topics", "/api/crawl"]:
            query = parse_qs(parsed.query)
            cat = query.get("category", ["all"])[0]
            try:
                topics = DefenseCrawler.fetch_multi_source_topics(category=cat, limit=20)
                self._send_json({"code": 200, "topics": topics})
            except Exception as e:
                logger.error(f"拉取情报异常: {e}")
                self._send_json({"code": 500, "message": str(e)})
            return

        # 4. [API] 健康检查: GET /api/health
        if path == "/api/health":
            self._send_json({
                "code": 200,
                "status": "healthy",
                "service": "wechat-auto-publisher",
                "version": "2.0.0"
            })
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. [API] 文章与配图生成 (流式思维与实时生成): POST /api/generate/stream
        if path == "/api/generate/stream":
            self._handle_generate_stream()
            return

        # 1.1 [API] 同步模式: POST /api/generate
        if path == "/api/generate":
            self._handle_generate()
            return

        # 2. [API] 一键推送草稿箱: POST /api/publish
        if path == "/api/publish":
            self._handle_publish()
            return

        self.send_error(404, "API Endpoint Not Found")

    def _serve_static_file(self, file_path: Path):
        """发送本地静态文件"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logger.error(f"发送静态文件失败 {file_path}: {e}")
            self.send_error(500, "Internal Server Error")

    def _handle_generate_stream(self):
        """处理研判文章与配图的 SSE 流式生成 (包含 DeepSeek-R1 深度思考链与正文流)"""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )

            topic = form.getvalue("topic", "").strip()
            raw_content = ""

            if "file" in form and form["file"].filename:
                file_item = form["file"]
                upload_dir = BASE_DIR / "storage" / "uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                saved_path = upload_dir / file_item.filename

                with open(saved_path, "wb") as f:
                    f.write(file_item.file.read())

                logger.info(f"接收到流式生成用户上传文件: {saved_path}")
                if saved_path.suffix.lower() == ".pdf":
                    raw_content = ContentParser.extract_from_pdf(str(saved_path))
                else:
                    raw_content = ContentParser.extract_from_text_file(str(saved_path))

            if not raw_content and topic:
                raw_content = f"焦点研判事件与指示：{topic}"

            if not raw_content:
                self._send_json({"code": 400, "message": "未接收到有效的研判事件或文件内容"})
                return

            # 设置 SSE 响应头
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            def send_sse(event_type: str, data_obj: Any):
                data_str = json.dumps(data_obj, ensure_ascii=False)
                payload = f"event: {event_type}" + chr(10) + f"data: {data_str}" + chr(10) + chr(10)
                self.wfile.write(payload.encode("utf-8"))
                self.wfile.flush()

            writer = AIWriter()
            final_article = None

            for evt in writer.generate_article_stream(raw_content=raw_content, user_focus=topic):
                evt_type = evt.get("type")
                evt_data = evt.get("data")

                if evt_type == "status":
                    send_sse("status", {"message": evt_data})
                elif evt_type == "think":
                    send_sse("think", {"text": evt_data})
                elif evt_type == "content":
                    send_sse("content", {"text": evt_data})
                elif evt_type == "done":
                    final_article = evt_data
                elif evt_type == "error":
                    send_sse("error", {"message": evt_data})
                    return

            if not final_article:
                send_sse("error", {"message": "AI 模型未返回有效生成内容"})
                return

            title = final_article.get("title", "深度防务研判")
            digest = final_article.get("digest", "观察全球防务与地缘博弈。")
            md_content = final_article.get("markdown_content", "")

            send_sse("status", {"message": "长文生成完毕，正在进行全自动军武配图与微信公众号专属内联排版..."})

            # 配图生成
            try:
                img_path = ImageService.generate_topic_image(topic=title, article_summary=digest)
                cover_path = CoverGenerator.crop_to_wechat_ratio(img_path)
            except Exception as e_img:
                logger.warning(f"配图生成异常，启用保底封面: {e_img}")
                cover_path = str(BASE_DIR / "assets" / "default_cover.jpg")

            # 微信公众号排版
            author_name = getattr(settings, "WECHAT_AUTHOR", getattr(settings, "WECHAT_DEFAULT_AUTHOR", "局势洞见"))
            html_content = WeChatFormatter.format_to_wechat_html(markdown_text=md_content, author=author_name)

            clean_text = "".join(md_content.split())
            word_count = len(clean_text)
            read_time = max(1, round(word_count / 380))

            CURRENT_CACHE["title"] = title
            CURRENT_CACHE["digest"] = digest
            CURRENT_CACHE["html_content"] = html_content
            CURRENT_CACHE["markdown_content"] = md_content
            CURRENT_CACHE["cover_image"] = cover_path
            CURRENT_CACHE["word_count"] = word_count
            CURRENT_CACHE["read_time"] = read_time

            send_sse("done", {
                "title": title,
                "digest": digest,
                "html_content": html_content,
                "markdown_content": md_content,
                "word_count": word_count,
                "read_time": read_time,
                "cover_image": cover_path,
                "thinking": final_article.get("thinking", "")
            })

        except Exception as e:
            logger.error(f"处理流式生成失败: {e}", exc_info=True)
            try:
                err_payload = "event: error" + chr(10) + f"data: {json.dumps({'message': str(e)})}" + chr(10) + chr(10)
                self.wfile.write(err_payload.encode("utf-8"))
                self.wfile.flush()
            except Exception:
                pass

    def _handle_generate(self):
        """处理研判文章与配图生成"""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )

            topic = form.getvalue("topic", "").strip()
            raw_content = ""

            # 处理上传的 PDF 或 TXT
            if "file" in form and form["file"].filename:
                file_item = form["file"]
                upload_dir = BASE_DIR / "storage" / "uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                saved_path = upload_dir / file_item.filename

                with open(saved_path, "wb") as f:
                    f.write(file_item.file.read())

                logger.info(f"接收到用户上传文件: {saved_path}")
                if saved_path.suffix.lower() == ".pdf":
                    raw_content = ContentParser.extract_from_pdf(str(saved_path))
                else:
                    raw_content = ContentParser.extract_from_text_file(str(saved_path))

            if not raw_content and topic:
                raw_content = f"焦点研判事件与指示：{topic}"

            if not raw_content:
                self._send_json({"code": 400, "message": "未接收到有效的报告内容或研判话题"})
                return

            # 1. 深度 AI 写作（聚焦来龙去脉与武器国家溯源）
            writer = AIWriter()
            article_data = writer.generate_article(raw_content=raw_content, user_focus=topic)

            title = article_data.get("title", "全球防务观察")
            digest = article_data.get("digest", "观察全球防务与地缘博弈。")
            md_content = article_data.get("markdown_content", "")

            # 2. 生成配图 (快手可图，带全套保底)
            try:
                img_path = ImageService.generate_topic_image(
                    topic=title,
                    article_summary=digest
                )
                cover_path = CoverGenerator.crop_to_wechat_ratio(img_path)
            except Exception as e_img:
                logger.warning(f"配图生成异常，启用保底封面: {e_img}")
                cover_path = str(BASE_DIR / "assets" / "default_cover.jpg")

            # 3. 微信专属内联样式排版
            author_name = getattr(settings, "WECHAT_AUTHOR", getattr(settings, "WECHAT_DEFAULT_AUTHOR", "局势洞见"))
            html_content = WeChatFormatter.format_to_wechat_html(
                markdown_text=md_content,
                author=author_name
            )

            # 统计字数
            clean_text = "".join(md_content.split())
            word_count = len(clean_text)
            read_time = max(1, round(word_count / 380))

            # 缓存生成结果
            CURRENT_CACHE["title"] = title
            CURRENT_CACHE["digest"] = digest
            CURRENT_CACHE["html_content"] = html_content
            CURRENT_CACHE["markdown_content"] = md_content
            CURRENT_CACHE["cover_image"] = cover_path
            CURRENT_CACHE["word_count"] = word_count
            CURRENT_CACHE["read_time"] = read_time

            self._send_json({
                "code": 200,
                "title": title,
                "digest": digest,
                "html_content": html_content,
                "word_count": word_count,
                "read_time": read_time,
                "cover_image": cover_path
            })

        except Exception as e:
            logger.error(f"处理生成请求失败: {e}", exc_info=True)
            self._send_json({"code": 500, "message": str(e)})

    def _handle_publish(self):
        """处理推送到微信公众号草稿箱"""
        try:
            if not CURRENT_CACHE["title"] or not CURRENT_CACHE["html_content"]:
                self._send_json({"code": 400, "message": "暂无待发布内容，请先执行生成！"})
                return

            wechat_client = WeChatClient()

            # 1. 上传永久封面
            logger.info("正在上传封面永久素材至微信 CDN...")
            thumb_media_id = wechat_client.upload_permanent_material(
                file_path=CURRENT_CACHE["cover_image"],
                material_type="image"
            )

            # 2. 创建图文草稿
            logger.info("正在推送至微信草稿箱...")
            article = {
                "title": CURRENT_CACHE["title"],
                "author": settings.WECHAT_AUTHOR,
                "digest": CURRENT_CACHE["digest"],
                "content": CURRENT_CACHE["html_content"],
                "thumb_media_id": thumb_media_id,
                "show_cover_pic": 1
            }

            media_id = wechat_client.add_draft(articles=[article])

            # 3. 记录已处理
            DefenseCrawler.save_history(CURRENT_CACHE["title"])

            # 4. 触发通知
            Notifier.send_all(
                title=f"【局势洞见】草稿推送成功: 《{CURRENT_CACHE['title']}》",
                content=(
                    f"文章标题：《{CURRENT_CACHE['title']}》\n"
                    f"文章字数：{CURRENT_CACHE.get('word_count', 0)} 字\n"
                    f"草稿 Media ID：{media_id}\n\n"
                    f"请在手机「订阅号助手」App 中审核后一键群发！"
                )
            )

            self._send_json({
                "code": 200,
                "message": "成功推送到微信公众平台草稿箱",
                "media_id": media_id
            })

        except Exception as e:
            logger.error(f"推送草稿箱失败: {e}", exc_info=True)
            self._send_json({"code": 500, "message": str(e)})
