# -*- coding: utf-8 -*-
"""
微信图文排版渲染引擎模块
职责：将 Markdown 格式的内容转换为符合微信富文本规范的高端内联 CSS（Inline CSS）HTML。
风格对标：顶级防务智库（白昃研究、华山穹剑、环球智库）风格——克制、沉稳、深海蓝与钛金灰质感。
特性支持：
1. 深度优化数据看板表格（Table / Thead / Tbody / Th / Td 自适应内联样式）；
2. 优化时间线与战术节点列表；
3. 强化 PART 胶囊标题与金句强调卡片；
4. 导读速览盒与智库文末声明。
"""

import re
import markdown
from typing import Dict, Any


class WeChatFormatter:
    """微信文章专属内联样式排版引擎"""

    # 核心视觉设计规范（纯 Inline CSS）
    STYLE_CONTAINER = (
        "margin: 0 auto; max-width: 677px; padding: 12px 14px; "
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; "
        "font-size: 15px; color: #2d3748; line-height: 1.8; letter-spacing: 0.5px; word-break: break-word;"
    )

    STYLE_LEAD_BOX = (
        "margin: 16px 0 24px 0; padding: 16px 18px; background-color: #f7fafc; "
        "border-left: 4px solid #1a365d; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); "
        "font-size: 14.5px; color: #334155; line-height: 1.75;"
    )

    STYLE_SECTION_H2 = (
        "margin: 36px 0 18px 0; padding-bottom: 10px; border-bottom: 1.5px solid #cbd5e1; "
        "display: flex; align-items: center;"
    )

    STYLE_H2_TAG = (
        "display: inline-block; background: linear-gradient(135deg, #1e3a8a, #0f172a); "
        "color: #ffffff; font-size: 11.5px; font-weight: 700; padding: 3px 9px; border-radius: 4px; "
        "margin-right: 10px; text-transform: uppercase; letter-spacing: 0.5px;"
    )

    STYLE_H2_TEXT = (
        "display: inline-block; font-size: 17.5px; font-weight: 700; color: #0f172a; "
        "letter-spacing: 0.5px;"
    )

    STYLE_H3_TEXT = (
        "margin: 24px 0 12px 0; font-size: 16px; font-weight: 700; color: #1d4ed8; "
        "border-left: 3.5px solid #2563eb; padding-left: 10px; line-height: 1.4;"
    )

    STYLE_P = "margin: 0 0 18px 0; font-size: 15.5px; color: #334155; line-height: 1.85; text-align: justify;"

    STYLE_QUOTE = (
        "margin: 22px 0; padding: 14px 18px; background: #f1f5f9; "
        "border-left: 4px solid #64748b; border-radius: 4px; "
        "font-style: normal; color: #475569; font-size: 14px; line-height: 1.75;"
    )

    STYLE_STRONG = "color: #1e3a8a; font-weight: 700;"

    STYLE_HR = "margin: 28px 0; border: 0; border-top: 1px dashed #cbd5e1;"

    # 强化表格内联样式（支持战役数据看板）
    STYLE_TABLE_WRAP = "margin: 22px 0; overflow-x: auto; -webkit-overflow-scrolling: touch;"
    STYLE_TABLE = "width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: left; line-height: 1.5; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"
    STYLE_TH = "background-color: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 12px; border: 1px solid #334155; font-size: 13px;"
    STYLE_TD = "padding: 9px 12px; border: 1px solid #e2e8f0; color: #334155; background-color: #ffffff; font-size: 13px;"

    # 列表样式
    STYLE_UL = "margin: 0 0 18px 0; padding-left: 20px; color: #334155;"
    STYLE_OL = "margin: 0 0 18px 0; padding-left: 22px; color: #334155;"
    STYLE_LI = "margin-bottom: 8px; font-size: 15px; line-height: 1.75;"

    STYLE_FOOTER = (
        "margin-top: 40px; padding: 20px 16px; background-color: #f8fafc; "
        "border-top: 2px solid #e2e8f0; border-radius: 6px; font-size: 13px; "
        "color: #64748b; line-height: 1.7; text-align: center;"
    )

    @classmethod
    def format_to_wechat_html(cls, markdown_text: str, author: str = "局势洞见研判组") -> str:
        """
        将标准 Markdown 转换为内联 CSS 样式的微信图文 HTML
        """
        # 1. 提取导读部分（如果有）
        lead_content = ""
        lead_match = re.search(r'【导读】[\s:：]*(.*?)(?=\n##|\n#|\Z)', markdown_text, re.DOTALL)
        if lead_match:
            lead_content = lead_match.group(1).strip()
            markdown_text = markdown_text.replace(lead_match.group(0), "")

        # 2. 基础 Markdown 转换，开启表格和常见扩展
        raw_html = markdown.markdown(
            markdown_text,
            extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists']
        )

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

        # 8. 注入内联样式：表格 <table>
        styled_html = re.sub(
            r'<table>(.*?)</table>',
            lambda m: f'<section style="{cls.STYLE_TABLE_WRAP}"><table style="{cls.STYLE_TABLE}">{m.group(1)}</table></section>',
            styled_html,
            flags=re.DOTALL
        )
        styled_html = re.sub(
            r'<th([^>]*)>(.*?)</th>',
            lambda m: f'<th style="{cls.STYLE_TH}">{m.group(2)}</th>',
            styled_html,
            flags=re.DOTALL
        )
        styled_html = re.sub(
            r'<td([^>]*)>(.*?)</td>',
            lambda m: f'<td style="{cls.STYLE_TD}">{m.group(2)}</td>',
            styled_html,
            flags=re.DOTALL
        )

        # 9. 注入内联样式：列表 <ul> <ol> <li>
        styled_html = re.sub(r'<ul>', f'<ul style="{cls.STYLE_UL}">', styled_html)
        styled_html = re.sub(r'<ol>', f'<ol style="{cls.STYLE_OL}">', styled_html)
        styled_html = re.sub(r'<li>(.*?)</li>', lambda m: f'<li style="{cls.STYLE_LI}">{m.group(1)}</li>', styled_html, flags=re.DOTALL)

        # 10. 注入内联样式：水平分割线 <hr>
        styled_html = re.sub(r'<hr\s*/?>', f'<hr style="{cls.STYLE_HR}" />', styled_html)

        # 11. 组装完整容器与头部、尾部
        lead_html = ""
        if lead_content:
            lead_html = f"""
            <section style="{cls.STYLE_LEAD_BOX}">
                <div style="font-weight: 700; color: #1a365d; margin-bottom: 8px; font-size: 13.5px; letter-spacing: 0.8px; display: flex; align-items: center;">
                    <span style="display:inline-block; width:4px; height:14px; background:#1a365d; margin-right:6px; border-radius:2px;"></span>
                    局势核心速览 · 战略研判要点
                </div>
                <div style="font-size:14.5px; color:#334155; line-height:1.75;">{lead_content}</div>
            </section>
            """

        footer_html = f"""
        <section style="{cls.STYLE_FOOTER}">
            <div style="font-weight: 700; color: #0f172a; font-size: 14.5px; margin-bottom: 6px;">
                【{author}】
            </div>
            <div style="color: #475569; font-size: 13.5px;">观察全球防务与地缘博弈。不跟风，不站队，只看事实与底层逻辑。</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 10px; border-top: 1px dashed #e2e8f0; padding-top: 8px;">
                * 声明：本文基于公开防务情报、专业战史智库及官方通报客观推演，文责自负，仅供交流研判。
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

    @classmethod
    def format_markdown(cls, markdown_text: str, author: str = "局势洞见") -> str:
        """别名方法"""
        return cls.format_to_wechat_html(markdown_text=markdown_text, author=author)
