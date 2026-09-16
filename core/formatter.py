# -*- coding: utf-8 -*-
"""
微信图文排版渲染引擎模块
职责：将 Markdown 格式的内容转换为符合微信富文本规范的高端内联 CSS（Inline CSS）HTML。
风格对标：顶级防务智库（白昃研究、华山穹剑、环球智库）风格——克制、沉稳、深海蓝与钛金灰质感。
"""

import re
import markdown
from typing import Dict, Any


class WeChatFormatter:
    """微信文章专属内联样式排版引擎"""

    # 核心视觉设计规范（纯 Inline CSS）
    STYLE_CONTAINER = (
        "margin: 0 auto; max-width: 677px; padding: 12px 16px; "
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; "
        "font-size: 15px; color: #2d3748; line-height: 1.8; letter-spacing: 0.5px; word-break: break-word;"
    )

    STYLE_LEAD_BOX = (
        "margin: 18px 0 26px 0; padding: 16px 18px; background-color: #f7fafc; "
        "border-left: 4px solid #1a365d; border-radius: 4px; "
        "font-size: 14.5px; color: #4a5568; line-height: 1.75;"
    )

    STYLE_SECTION_H2 = (
        "margin: 32px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; "
        "display: flex; align-items: center;"
    )

    STYLE_H2_TAG = (
        "display: inline-block; background-color: #1a365d; color: #ffffff; "
        "font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 2px; "
        "margin-right: 8px; text-transform: uppercase;"
    )

    STYLE_H2_TEXT = (
        "display: inline-block; font-size: 17px; font-weight: 700; color: #1a202c; "
        "letter-spacing: 0.5px;"
    )

    STYLE_H3_TEXT = (
        "margin: 22px 0 10px 0; font-size: 15.5px; font-weight: 700; color: #2b6cb0; "
        "border-left: 3px solid #2b6cb0; padding-left: 8px;"
    )

    STYLE_P = "margin: 0 0 16px 0; font-size: 15px; color: #2d3748; line-height: 1.8; text-align: justify;"

    STYLE_QUOTE = (
        "margin: 20px 0; padding: 14px 18px; background: #edf2f7; "
        "border-left: 3px solid #718096; border-radius: 2px; "
        "font-style: normal; color: #4a5568; font-size: 14px; line-height: 1.7;"
    )

    STYLE_STRONG = "color: #1a365d; font-weight: 700;"

    STYLE_FACT_BOX = (
        "margin: 20px 0; padding: 14px 16px; background-color: #fffaf0; "
        "border: 1px solid #feebc8; border-radius: 4px; font-size: 14px; color: #7b341e;"
    )

    STYLE_FOOTER = (
        "margin-top: 40px; padding: 20px 16px; background-color: #f7fafc; "
        "border-radius: 6px; text-align: center; font-size: 13px; color: #718096; line-height: 1.6;"
    )

    @classmethod
    def format_markdown_to_wechat_html(cls, md_text: str, author: str = "局势洞见") -> str:
        """
        将结构化 Markdown 内容渲染为自带高端质感内联 CSS 的微信富文本 HTML
        """
        # 1. 预处理 Markdown：提取导语块（如果存在）
        lead_content = ""
        lead_match = re.search(r'>\s*【导读】(.*?)(?=\n\n|\n#|$)', md_text, re.DOTALL)
        if lead_match:
            lead_content = lead_match.group(1).strip()
            # 移除原 Markdown 里的导读标记
            md_text = md_text.replace(lead_match.group(0), "")

        # 2. 转换为标准 HTML
        raw_html = markdown.markdown(md_text, extensions=['extra', 'tables'])

        # 3. 注入内联样式：段落 <p>
        styled_html = re.sub(
            r'<p>(.*?)</p>',
            lambda m: f'<p style="{cls.STYLE_P}">{m.group(1)}</p>',
            raw_html,
            flags=re.DOTALL
        )

        # 4. 注入内联样式：加粗 <strong>
        styled_html = re.sub(
            r'<strong>(.*?)</strong>',
            lambda m: f'<strong style="{cls.STYLE_STRONG}">{m.group(1)}</strong>',
            styled_html
        )

        # 5. 注入内联样式：二级标题 <h2>
        def replace_h2(match):
            title = match.group(1).strip()
            # 自动提取数字标识（如果有，例如 "01 战局复盘"）
            num_match = re.match(r'^([0-9A-Za-z一二三四五六七八九十]+)[\s、.:](.*)', title)
            if num_match:
                tag_num = num_match.group(1)
                text_part = num_match.group(2)
                return (
                    f'<section style="{cls.STYLE_SECTION_H2}">'
                    f'<span style="{cls.STYLE_H2_TAG}">PART {tag_num}</span>'
                    f'<span style="{cls.STYLE_H2_TEXT}">{text_part}</span>'
                    f'</section>'
                )
            return (
                f'<section style="{cls.STYLE_SECTION_H2}">'
                f'<span style="{cls.STYLE_H2_TAG}">FOCUS</span>'
                f'<span style="{cls.STYLE_H2_TEXT}">{title}</span>'
                f'</section>'
            )

        styled_html = re.sub(r'<h2>(.*?)</h2>', replace_h2, styled_html)

        # 6. 注入内联样式：三级标题 <h3>
        styled_html = re.sub(
            r'<h3>(.*?)</h3>',
            lambda m: f'<h3 style="{cls.STYLE_H3_TEXT}">{m.group(1)}</h3>',
            styled_html
        )

        # 7. 注入内联样式：引用块 <blockquote>
        styled_html = re.sub(
            r'<blockquote>\s*(?:<p[^>]*>)?(.*?)(?:</p>)?\s*</blockquote>',
            lambda m: f'<blockquote style="{cls.STYLE_QUOTE}">{m.group(1)}</blockquote>',
            styled_html,
            flags=re.DOTALL
        )

        # 8. 组装完整内联容器与头部、尾部
        lead_html = ""
        if lead_content:
            lead_html = f"""
            <section style="{cls.STYLE_LEAD_BOX}">
                <div style="font-weight: 700; color: #1a365d; margin-bottom: 6px; font-size: 13px; letter-spacing: 1px;">
                    ■ 局势速览 / EXECUTIVE SUMMARY
                </div>
                <div>{lead_content}</div>
            </section>
            """

        footer_html = f"""
        <section style="{cls.STYLE_FOOTER}">
            <div style="font-weight: 700; color: #1a365d; font-size: 14px; margin-bottom: 6px;">
                【{author}】
            </div>
            <div>观察全球防务与地缘博弈。不跟风，不站队，只看事实与底层逻辑。</div>
            <div style="font-size: 12px; color: #a0aec0; margin-top: 8px;">
                * 本文基于公开情报、智库报告及官方通报客观研判，仅供参考。
            </div>
        </section>
        """

        full_article_html = f"""
        <section style="{cls.STYLE_CONTAINER}">
            {lead_html}
            {styled_html}
            {footer_html}
        </section>
        """
        return full_article_html
