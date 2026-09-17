# -*- coding: utf-8 -*-
"""
Web 控制台请求处理核心模块
职责：
1. 托管控制台前端静态资源；
2. 提供热点情报抓取与历史过滤 API；
3. 处理 SSE 流式深度思考与全文生成长连接；
4. 提供 4 大排版主题实时预览与多风格 AI 出图 API；
5. 提供 SQLite 历史文章文库调阅与一键重推 API；
6. 微信公众号草稿箱真实对接发布。
"""

import os
import datetime
import json
import cgi
import mimetypes
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict

from config.settings import logger, BASE_DIR
from config import settings
from core.crawler import DefenseCrawler
from core.content_parser import ContentParser
from core.ai_writer import AIWriter
from core.formatter import WeChatFormatter
from core.cover_generator import CoverGenerator
from core.image_service import ImageService
from core.matrix_adapter import MatrixAdapter
from core.prompt_manager import PromptManager
from core.db import DatabaseManager
from core.strategy import StrategyManager, AIStrategist
from core.wechat_api import WeChatClient
from notify.notifier import Notifier

STATIC_DIR = BASE_DIR / "static"

CURRENT_CACHE: Dict[str, Any] = {
    "article_id": 0,
    "title": "",
    "digest": "",
    "html_content": "",
    "markdown_content": "",
    "theme": "think_tank",
    "cover_image": "",
    "illustration_prompt": "",
    "word_count": 0,
    "read_time": 1,
    "douyin_script": "",
    "xiaohongshu_note": ""
}


class AppAPIHandler(SimpleHTTPRequestHandler):
    PublisherHTTPHandler = None
    """自定义 HTTP 请求处理器"""

    def do_OPTIONS(self):
        """处理预检跨域请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. 首页静态页面
        if path == "/" or path == "/index.html":
            self._serve_static_file(STATIC_DIR / "index.html")
            return

        # 2. 静态文件托管
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            target_file = STATIC_DIR / rel_path
            if target_file.exists() and target_file.is_file():
                self._serve_static_file(target_file)
                return
            self.send_error(404, "Static File Not Found")
            return

        # 3. 本地图片/资源临时预览 (/assets/...)
        if path.startswith("/assets/"):
            rel_path = path[len("/assets/"):]
            target_file = BASE_DIR / "assets" / rel_path
            if target_file.exists() and target_file.is_file():
                self._serve_static_file(target_file)
                return
            self.send_error(404, "Asset Not Found")
            return

        # 4. [API] 探测情报与战报列表: GET /api/topics 或 GET /api/crawl
        if path in ["/api/topics", "/api/crawl"]:
            query = parse_qs(parsed.query)
            cat = query.get("category", ["all"])[0]
            clustered = query.get("clustered", ["1"])[0]
            force_refresh = (query.get("refresh", ["0"])[0] == "1")
            try:
                if clustered == "1":
                    clusters = DefenseCrawler.fetch_clustered_topics(category=cat, limit=25, force_refresh=force_refresh)
                    all_items = []
                    for c in clusters:
                        all_items.extend(c.get("items", []))
                    if all_items:
                        DatabaseManager.record_news_items(all_items)

                    # 按照用户截图标准体系，生成丰富的宏观领域分类胶囊 (全部、国内、科技、军事、国际、民生)
                    cat_order = [
                        {"id": "all", "name": "全部"},
                        {"id": "domestic", "name": "国内"},
                        {"id": "tech", "name": "科技"},
                        {"id": "military", "name": "军事"},
                        {"id": "intl", "name": "国际"},
                        {"id": "livelihood", "name": "民生"},
                    ]
                    dynamic_categories = []
                    for cat_def in cat_order:
                        cid = cat_def["id"]
                        if cid == "all":
                            cnt = len(clusters)
                            dynamic_categories.append({"id": cid, "name": cat_def["name"], "count": cnt})
                        else:
                            cnt = sum(1 for c in clusters if c.get("category") == cid or c.get("badge") == cat_def["name"])
                            if cnt > 0:
                                dynamic_categories.append({"id": cid, "name": cat_def["name"], "count": cnt})
                    self._send_json({"code": 200, "clusters": clusters, "dynamic_categories": dynamic_categories, "raw_topics": all_items})
                else:
                    topics = DefenseCrawler.fetch_multi_source_topics(category=cat, limit=25)
                    DatabaseManager.record_news_items(topics)
                    self._send_json({"code": 200, "topics": topics})
            except Exception as e:
                logger.error(f"拉取情报异常: {e}")
                self._send_json({"code": 500, "message": str(e)})
            return

        # 5. [API] 获取智库提示词配置: GET /api/prompts
        if path == "/api/prompts":
            prompts = PromptManager.get_prompts()
            self._send_json({"code": 200, **prompts})
            return

        # 6. [API] 获取 SQLite 历史文章列表: GET /api/articles/history
        if path == "/api/articles/history":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", [20])[0])
            articles = DatabaseManager.get_recent_articles(limit=limit)
            self._send_json({"code": 200, "articles": articles})
            return

        # 7. [API] 获取指定历史文章详情: GET /api/articles/get
        if path == "/api/articles/get":
            query = parse_qs(parsed.query)
            art_id = int(query.get("id", [0])[0])
            art = DatabaseManager.get_article_by_id(art_id)
            if art:
                # 载入到当前内存缓存，便于用户一键重推
                CURRENT_CACHE["article_id"] = art["id"]
                CURRENT_CACHE["title"] = art["title"]
                CURRENT_CACHE["digest"] = art.get("lead", "")
                CURRENT_CACHE["html_content"] = art.get("wechat_html", "")
                CURRENT_CACHE["markdown_content"] = art.get("markdown_content", "")
                CURRENT_CACHE["theme"] = art.get("theme", "think_tank")
                CURRENT_CACHE["cover_image"] = art.get("cover_image_path", "")
                CURRENT_CACHE["douyin_script"] = art.get("douyin_script", "")
                CURRENT_CACHE["xiaohongshu_note"] = art.get("xiaohongshu_note", "")
                self._send_json({"code": 200, "article": art})
            else:
                self._send_json({"code": 404, "message": "未找到指定历史文章"})
            return

        # 8. [API] 获取所有支持的主题与视觉风格列表: GET /api/themes
        if path == "/api/themes":
            self._send_json({
                "code": 200,
                "themes": WeChatFormatter.THEMES,
                "visual_styles": ImageService.VISUAL_STYLES
            })
            return

        # 8.1 [API] 获取当前生效的智库策略与对话历史: GET /api/strategy/current
        if path == "/api/strategy/current":
            strategy = StrategyManager.load_strategy()
            self._send_json({"code": 200, "strategy": strategy})
            return

        # 9. [API] 健康检查
        if path == "/api/health":
            self._send_json({
                "code": 200,
                "status": "healthy",
                "service": "wechat-auto-publisher",
                "version": "3.0.0-pro"
            })
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 0.01 [API] 与 AI 策略总监对话交互调优: POST /api/strategy/chat
        if path == "/api/strategy/chat":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                data = json.loads(body)
                msg = data.get("message", "").strip()
                if not msg:
                    self._send_json({"code": 400, "message": "消息内容不能为空"})
                    return
                res = AIStrategist.chat_tune(msg)
                self._send_json({"code": 200, **res})
            except Exception as e:
                logger.error(f"策略对话异常: {e}")
                self._send_json({"code": 500, "message": str(e)})
            return

        # 0.02 [API] 重置智库策略为默认状态: POST /api/strategy/reset
        if path == "/api/strategy/reset":
            StrategyManager.save_strategy(StrategyManager.DEFAULT_STRATEGY.copy())
            self._send_json({"code": 200, "strategy": StrategyManager.DEFAULT_STRATEGY})
            return

        # 0.03 [API] AI 自动推演并刷新今日雷达词: POST /api/strategy/radar_refresh
        if path == "/api/strategy/radar_refresh":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                titles = []
                if content_len > 0:
                    body = self.rfile.read(content_len).decode("utf-8")
                    data = json.loads(body)
                    titles = data.get("titles", [])
                kws = AIStrategist.refresh_daily_radar(titles)
                self._send_json({"code": 200, "active_keywords": kws})
            except Exception as e:
                logger.error(f"刷新雷达异常: {e}")
                self._send_json({"code": 500, "message": str(e)})
            return

        # 0.1 [API] 按需搜集政府与外交部官方公告: POST /api/topics/expand_sources
        if path == "/api/topics/expand_sources":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                data = json.loads(body)
                kw = data.get("keyword", "")
                c_name = data.get("cluster_name", "")
                officials = DefenseCrawler.search_official_statements(keyword=kw, cluster_name=c_name)
                self._send_json({"code": 200, "items": officials})
            except Exception as e:
                logger.error(f"扩展官方信源失败: {e}")
                self._send_json({"code": 500, "message": str(e)})
            return

        # 0. [API] 单篇/多篇新闻正文实时抓取: POST /api/topics/fetch_content
        if path == "/api/topics/fetch_content":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                data = json.loads(body)
                url = data.get("url", "")
                text = DefenseCrawler.fetch_article_content(url) if url else ""
                self._send_json({"code": 200, "content": text})
            except Exception as e:
                self._send_json({"code": 500, "message": str(e)})
            return

        # 1. [API] 文章与配图生成 (流式深度思考): POST /api/generate/stream
        if path == "/api/generate/stream":
            self._handle_generate_stream()
            return

        # 2. [API] 同步模式生成: POST /api/generate
        if path == "/api/generate":
            self._handle_generate()
            return

        # 3. [API] 实时主题格式化预览: POST /api/format/preview
        if path == "/api/format/preview":
            self._handle_format_preview()
            return

        # 4. [API] 独立视觉配图生成: POST /api/generate/image
        if path == "/api/generate/image":
            self._handle_generate_image()
            return

        # 5. [API] 恢复默认提示词: POST /api/prompts/reset
        if path == "/api/prompts/reset":
            res = PromptManager.reset_prompts()
            self._send_json({"code": 200, "message": "已恢复智库默认提示词", **res})
            return

        # 6. [API] 保存修改后的提示词: POST /api/prompts
        if path == "/api/prompts":
            self._handle_save_prompts()
            return

        # 7. [API] 一键推送草稿箱: POST /api/publish
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

    def _handle_format_preview(self):
        """实时将 Markdown 格式化为选定主题的微信 HTML"""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            md_text = data.get("markdown", "") or CURRENT_CACHE.get("markdown_content", "")
            theme_key = data.get("theme", "think_tank")
            author = data.get("author", "局势洞见研判组")

            article_images = []
            if CURRENT_CACHE.get("cover_image"):
                cov = CURRENT_CACHE["cover_image"]
                rel_url = "/" + str(Path(cov).relative_to(BASE_DIR) if BASE_DIR in Path(cov).parents else cov)
                article_images.append({"url": rel_url, "caption": "▲ 战区现场实录与核心交锋装备态势"})
            if (BASE_DIR / "assets" / "tactical_situation.jpg").exists():
                article_images.append({"url": "/assets/tactical_situation.jpg", "caption": "▲ 战术态势推演：关键海域防空雷达探测盲区与突防弹道示意"})

            sources_list = CURRENT_CACHE.get("sources_list") or [
                f"防务官方通报与公开战报研判池 ({datetime.datetime.now().strftime('%Y-%m-%d')})",
                "全球海事安全通报与雷达侦测遥感情报"
            ]

            html = WeChatFormatter.format_to_wechat_html(
                md_text,
                theme_name=theme_key,
                author=author,
                images=article_images,
                sources=sources_list
            )
            CURRENT_CACHE["html_content"] = html
            CURRENT_CACHE["theme"] = theme_key

            self._send_json({
                "code": 200,
                "html": html,
                "theme": theme_key
            })
        except Exception as e:
            logger.error(f"格式化预览失败: {e}")
            self._send_json({"code": 500, "message": str(e)})

    def _handle_generate_image(self):
        """生成指定风格的配图与杂志封面"""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            prompt = data.get("prompt", "").strip() or CURRENT_CACHE.get("title", "前沿战术推演")
            style_key = data.get("style", "photojournalism")
            category = data.get("category", "国际防务特刊")

            img_path = ImageService.generate_image_by_flux(prompt, style_key=style_key)
            cover_path = CoverGenerator.crop_to_wechat_ratio(
                img_path,
                title=CURRENT_CACHE.get("title", prompt),
                category=category,
                style="magazine"
            )

            CURRENT_CACHE["cover_image"] = cover_path
            CURRENT_CACHE["illustration_prompt"] = prompt

            self._send_json({
                "code": 200,
                "cover_image": cover_path,
                "prompt": prompt,
                "style": style_key
            })
        except Exception as e:
            logger.error(f"独立生图失败: {e}")
            self._send_json({"code": 500, "message": str(e)})

    def _handle_generate_stream(self):
        """处理研判文章与配图的 SSE 流式生成"""
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
            theme_choice = form.getvalue("theme", "think_tank").strip()
            image_style = form.getvalue("image_style", "photojournalism").strip()
            selected_articles_str = form.getvalue("selected_articles", "").strip()
            raw_content = ""
            _source_news_json = "[]"

            # 优先从多选新闻中并发抓取真实正文并组装多源情报包
            if selected_articles_str:
                try:
                    articles_list = json.loads(selected_articles_str)
                    if isinstance(articles_list, list) and len(articles_list) > 0:
                        packet_lines = [f"【多源实时战略情报输入包 · 采样基准：{datetime.datetime.now().strftime('%Y年%m月%d日')}】\n"]
                        for idx, art in enumerate(articles_list):
                            url = art.get("url", "")
                            title = art.get("title", "")
                            source = art.get("source", "权威公开报道")
                            pub_time = art.get("pub_time", "实时")
                            logger.info(f"正在深度抓取情报源 [{idx+1}] 正文全文: {title[:20]}...")
                            fetched_text = DefenseCrawler.fetch_article_content(url) if url else ""
                            article_text = fetched_text or art.get("summary", "") or "依托公开现场战报要点"
                            packet_lines.append(f"""
---
[情报源 {idx+1}] {source} (发布时间：{pub_time})
标题：《{title}》
原文链接：{url}
现场报道详细正文：
{article_text}
""")
                        raw_content = "\n".join(packet_lines)
                        # 记录来源新闻列表，用于历史追溯
                        import json as _json
                        _source_news_json = _json.dumps([
                            {"title": a.get("title",""), "source": a.get("source",""), "url": a.get("url",""), "pub_time": a.get("pub_time","")}
                            for a in articles_list
                        ], ensure_ascii=False)
                except Exception as e_parse:
                    logger.warning(f"解析多选新闻材料失败: {e_parse}")

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
                self._send_json({"code": 400, "message": "未接收到有效的研判事件或文件内容"})
                return

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

            send_sse("status", {"message": f"长文生成完毕，正在根据 [{image_style}] 风格生成视觉配图与封面..."})

            # 1. 自动生成正文双图 (图一: 场景实录大片, 图二: 战术态势示意图) 与封面
            try:
                send_sse("status", {"message": f"长文初稿就绪，正在生成场景实录大片与战术态势示意图..."})
                img1_path = ImageService.generate_image_by_flux(prompt=title, style_key=image_style)
                cover_path = CoverGenerator.crop_to_wechat_ratio(
                    img1_path,
                    title=title,
                    category=topic[:12] if topic else "战略研判",
                    style="magazine"
                )
            except Exception as e_img:
                logger.warning(f"实景大片生成异常: {e_img}")
                cover_path = str(BASE_DIR / "assets" / "article_cover.jpg")
                img1_path = cover_path

            # 图二: 战术态势推演示意图 (带有战术雷达波与坐标标注)
            try:
                img2_path = ImageService.generate_tactical_infographic(
                    title=title,
                    label=f"{datetime.datetime.now().year} 多波次攻防推演与雷达盲区示意",
                    output_path="assets/tactical_situation.jpg"
                )
            except Exception as e_tac:
                logger.warning(f"战术态势图合成异常: {e_tac}")
                img2_path = ""

            # 构造内嵌图片列表 (本地相对路径或 CDN)
            article_images = []
            if img1_path:
                article_images.append({
                    "url": "/" + str(Path(img1_path).relative_to(BASE_DIR) if BASE_DIR in Path(img1_path).parents else img1_path),
                    "caption": f"▲ 战区现场实录与核心交锋装备态势 ({image_style})"
                })
            if img2_path:
                article_images.append({
                    "url": "/" + str(Path(img2_path).relative_to(BASE_DIR) if BASE_DIR in Path(img2_path).parents else img2_path),
                    "caption": "▲ 战术态势推演：关键海域防空雷达探测盲区与突防弹道示意"
                })

            # 2. 构造信源清单 (事实核查附录)
            sources_list = []
            if selected_articles_str:
                try:
                    arts = json.loads(selected_articles_str)
                    for a in arts:
                        sources_list.append(f"{a.get('source', '权威媒体')}：{a.get('title', '')} ({a.get('pub_time', '实时')})")
                except Exception:
                    pass
            if not sources_list:
                sources_list = [
                    f"防务官方通报与公开战报研判池 ({datetime.datetime.now().strftime('%Y-%m-%d')})",
                    "全球海事安全通报与雷达侦测遥感情报"
                ]

            # 3. 微信公众号主题排版 (内嵌双图与信源附录)
            author_name = getattr(settings, "WECHAT_AUTHOR", "局势洞见研判组")
            html_content = WeChatFormatter.format_to_wechat_html(
                markdown_text=md_content,
                theme_name=theme_choice,
                author=author_name,
                images=article_images,
                sources=sources_list
            )

            clean_text = "".join(md_content.split())
            word_count = len(clean_text)
            read_time = max(1, round(word_count / 380))

            # 矩阵内容变型派生 (抖音与小红书)
            matrix_res = MatrixAdapter.adapt_all(title=title, digest=digest, markdown_content=md_content)
            douyin_script = matrix_res["douyin"]
            xiaohongshu_note = matrix_res["xiaohongshu"]

            # 持久化到 SQLite
            art_id = DatabaseManager.save_article(
                title=title,
                category=topic[:20] if topic else "前沿热点",
                theme=theme_choice,
                author=author_name,
                lead=digest,
                markdown_content=md_content,
                wechat_html=html_content,
                douyin_script=douyin_script,
                xiaohongshu_note=xiaohongshu_note,
                cover_image_path=cover_path,
                illustration_prompt=title,
                source_news_json=_source_news_json
            )

            CURRENT_CACHE["article_id"] = art_id
            CURRENT_CACHE["title"] = title
            CURRENT_CACHE["digest"] = digest
            CURRENT_CACHE["html_content"] = html_content
            CURRENT_CACHE["markdown_content"] = md_content
            CURRENT_CACHE["theme"] = theme_choice
            CURRENT_CACHE["cover_image"] = cover_path
            CURRENT_CACHE["word_count"] = word_count
            CURRENT_CACHE["read_time"] = read_time
            CURRENT_CACHE["douyin_script"] = douyin_script
            CURRENT_CACHE["xiaohongshu_note"] = xiaohongshu_note

            send_sse("done", {
                "id": art_id,
                "title": title,
                "digest": digest,
                "theme": theme_choice,
                "html_content": html_content,
                "markdown_content": md_content,
                "word_count": word_count,
                "read_time": read_time,
                "cover_image": cover_path,
                "thinking": final_article.get("thinking", ""),
                "douyin_script": douyin_script,
                "xiaohongshu_note": xiaohongshu_note
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
        """同步生成模式"""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            topic = data.get("topic", "").strip()
            theme_choice = data.get("theme", "think_tank").strip()
            image_style = data.get("image_style", "photojournalism").strip()

            writer = AIWriter()
            res = writer.generate_article(raw_content=f"焦点研判事件：{topic}", user_focus=topic)

            title = res.get("title", "深度防务研判")
            digest = res.get("digest", "")
            md_content = res.get("markdown_content", "")

            img_path = ImageService.generate_image_by_flux(prompt=title, style_key=image_style)
            cover_path = CoverGenerator.crop_to_wechat_ratio(img_path, title=title, category=topic[:12], style="magazine")

            author_name = getattr(settings, "WECHAT_AUTHOR", "局势洞见研判组")
            html_content = WeChatFormatter.format_to_wechat_html(md_content, theme_name=theme_choice, author=author_name)

            clean_text = "".join(md_content.split())
            word_count = len(clean_text)
            read_time = max(1, round(word_count / 380))

            matrix_res = MatrixAdapter.adapt_all(title=title, digest=digest, markdown_content=md_content)
            douyin_script = matrix_res["douyin"]
            xiaohongshu_note = matrix_res["xiaohongshu"]

            _source_news_json = "[]"
            art_id = DatabaseManager.save_article(
                title=title,
                category=topic[:20] if topic else "前沿热点",
                theme=theme_choice,
                author=author_name,
                lead=digest,
                markdown_content=md_content,
                wechat_html=html_content,
                douyin_script=douyin_script,
                xiaohongshu_note=xiaohongshu_note,
                cover_image_path=cover_path,
                illustration_prompt=title,
                source_news_json=_source_news_json
            )

            CURRENT_CACHE["article_id"] = art_id
            CURRENT_CACHE["title"] = title
            CURRENT_CACHE["digest"] = digest
            CURRENT_CACHE["html_content"] = html_content
            CURRENT_CACHE["markdown_content"] = md_content
            CURRENT_CACHE["theme"] = theme_choice
            CURRENT_CACHE["cover_image"] = cover_path
            CURRENT_CACHE["word_count"] = word_count
            CURRENT_CACHE["read_time"] = read_time
            CURRENT_CACHE["douyin_script"] = douyin_script
            CURRENT_CACHE["xiaohongshu_note"] = xiaohongshu_note

            self._send_json({
                "code": 200,
                "id": art_id,
                "title": title,
                "digest": digest,
                "theme": theme_choice,
                "html_content": html_content,
                "word_count": word_count,
                "read_time": read_time,
                "cover_image": cover_path,
                "douyin_script": douyin_script,
                "xiaohongshu_note": xiaohongshu_note
            })

        except Exception as e:
            logger.error(f"处理同步生成请求失败: {e}", exc_info=True)
            self._send_json({"code": 500, "message": str(e)})

    def _handle_save_prompts(self):
        """处理提示词更新保存"""
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)
            sys_p = data.get("system_prompt", "")
            user_p = data.get("user_prompt_template", "")

            if not sys_p or not user_p:
                self._send_json({"code": 400, "message": "提示词内容不能为空"})
                return

            PromptManager.save_prompts(sys_p, user_p)
            self._send_json({"code": 200, "message": "智库提示词配置已成功保存并立即生效"})
        except Exception as e:
            logger.error(f"保存提示词失败: {e}")
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
                "author": getattr(settings, "WECHAT_AUTHOR", "局势洞见研判组"),
                "digest": CURRENT_CACHE["digest"],
                "content": CURRENT_CACHE["html_content"],
                "thumb_media_id": thumb_media_id,
                "show_cover_pic": 1
            }

            media_id = wechat_client.add_draft(articles=[article])

            # 3. 更新 SQLite 中的发布状态
            if CURRENT_CACHE.get("article_id"):
                DatabaseManager.update_article_publish_status(
                    article_id=CURRENT_CACHE["article_id"],
                    wechat_media_id=media_id,
                    status="published"
                )

            # 4. 记录已处理
            DefenseCrawler.save_history(CURRENT_CACHE["title"])

            # 5. 触发通知
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

    def _send_json(self, data: dict, status_code: int = 200):
        """标准 JSON 响应工具函数"""
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

PublisherHTTPHandler = AppAPIHandler
