# -*- coding: utf-8 -*-
"""
微信公众号全自动发布系统 - 主控制入口
执行流程：
1. 解析指定素材（PDF智库报告 / 网页文章 / 热点焦点）；
2. 调度 AI 写作引擎按《局势洞见》冷峻风格深度撰写；
3. 将 Markdown 内容渲染为微信专属内联 CSS 富文本 HTML；
4. 准备或自动生成 2.35:1 比例高质感封面图；
5. 调用微信公众平台 API 上传素材并写入草稿箱；
6. 触发手机微信通知（PushPlus/Server酱）。
"""

import sys
import argparse
from pathlib import Path

from config.settings import settings, logger
from core import WeChatClient, ContentParser, AIWriter, WeChatFormatter, CoverGenerator
from notify import Notifier


def process_pipeline(
    file_path: str = None,
    url: str = None,
    topic: str = None,
    cover_image: str = None,
    dry_run: bool = False
):
    """端到端核心处理流水线"""
    logger.info("==================================================")
    logger.info("🚀 启动微信公众号内容生产与发布流水线")
    logger.info("==================================================")

    # 1. 提取素材内容
    raw_content = ""
    if file_path:
        f_path = Path(file_path)
        if not f_path.exists():
            logger.error(f"指定素材文件未找到: {file_path}")
            return
        if f_path.suffix.lower() == ".pdf":
            raw_content = ContentParser.extract_from_pdf(str(f_path))
        else:
            raw_content = ContentParser.extract_from_text_file(str(f_path))
    elif url:
        raw_content = ContentParser.extract_from_url(url)
    elif topic:
        raw_content = f"请围绕当前焦点话题进行深度智库研判：{topic}"
    else:
        logger.error("必须至少提供 --file、--url 或 --topic 之一作为素材源！")
        return

    if not raw_content or len(raw_content.strip()) < 30:
        logger.error("提取的素材内容过短或为空，无法进行深度撰写。")
        return

    # 2. AI 深度改写与内容构建
    writer = AIWriter()
    try:
        article_data = writer.generate_article(raw_content, user_focus=topic or "")
    except Exception as e:
        logger.error(f"AI 生成文章失败: {e}")
        return

    title = article_data.get("title", "防务观察特稿")
    digest = article_data.get("digest", "")
    markdown_content = article_data.get("markdown_content", "")

    # 3. 渲染为微信富文本 HTML (带内联 CSS)
    html_content = WeChatFormatter.format_markdown_to_wechat_html(
        markdown_content,
        author=settings.WECHAT_DEFAULT_AUTHOR
    )

    # 保存一份本地预览 HTML 供调试核对
    preview_path = Path("scratch/preview.html")
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"本地排版效果预览已生成: {preview_path.resolve()}")

    if dry_run:
        logger.info("【本地测试模式 (Dry-Run)】已跳过微信接口上传与手机推送。")
        print(f"\n[生成标题]: {title}")
        print(f"[文章摘要]: {digest}")
        print(f"[预览文件]: {preview_path.resolve()}\n")
        return

    # 4. 验证微信配置
    if not settings.validate_wechat_credentials():
        logger.error("微信凭据未填写，无法推送到公众号。请先在 .env 中配置 WECHAT_APPID 和 WECHAT_APPSECRET。")
        return

    # 5. 准备封面图并上传永久素材
    if not cover_image or not Path(cover_image).exists():
        cover_image = CoverGenerator.generate_default_cover(title)

    wechat = WeChatClient()
    try:
        thumb_media_id = wechat.upload_thumb_material(cover_image)
    except Exception as e:
        logger.error(f"上传封面素材失败: {e}")
        return

    # 6. 推送到微信草稿箱
    try:
        draft_media_id = wechat.create_draft(
            title=title,
            content_html=html_content,
            thumb_media_id=thumb_media_id,
            digest=digest
        )
    except Exception as e:
        logger.error(f"提交草稿箱失败: {e}")
        return

    # 7. 手机端实时通知
    Notifier.notify_publish_success(title, digest, draft_media_id)

    logger.info("==================================================")
    logger.info(f"🎉 全部流程圆满完成！草稿已进入公众号后台：")
    logger.info(f"👉 标题: {title}")
    logger.info(f"👉 草稿 ID: {draft_media_id}")
    logger.info("请使用手机微信打开「订阅号助手」App，即可一键群发！")
    logger.info("==================================================")


def main():
    parser = argparse.ArgumentParser(description="微信公众号自动撰写与草稿推送系统")
    parser.add_argument("--file", "-f", type=str, help="本地素材路径 (PDF / TXT / MD 报告)")
    parser.add_argument("--url", "-u", type=str, help="文章/新闻参考链接")
    parser.add_argument("--topic", "-t", type=str, help="直接指定热点话题/研判方向")
    parser.add_argument("--cover", "-c", type=str, help="指定封面图片路径 (默认自动生成)")
    parser.add_argument("--dry-run", action="store_true", help="本地预览调试模式，不向微信上传")

    args = parser.parse_args()

    if not any([args.file, args.url, args.topic]):
        print("\n使用示例：")
        print("1. 从 PDF 报告生成: python main.py --file /path/to/胡塞武装与沙特冲突舆情报告.pdf")
        print("2. 从热点话题生成: python main.py --topic '曼德海峡地缘博弈与美军航母困境'")
        print("3. 本地仅排版预览: python main.py --topic '美军间谍船遭袭事件' --dry-run\n")
        parser.print_help()
        sys.exit(1)

    process_pipeline(
        file_path=args.file,
        url=args.url,
        topic=args.topic,
        cover_image=args.cover,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
