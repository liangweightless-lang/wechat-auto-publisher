# -*- coding: utf-8 -*-
"""
微信图文专业排版格式化模块 (支持 4 大主题与 6 大富文本排版组件)
职责：
1. 将标准 Markdown 深度渲染为 100% 微信富文本内联样式（Inline CSS）；
2. 内置 4 套顶尖专业智库排版主题（权威智库 / 硬核防务 / 地缘博弈 / 战地特稿）；
3. 原生支持 6 大微信硬核富文本内联组件（金句卡、时序时间轴、红蓝对抗VS卡、指标看板、战术小贴士、斑马对比表）；
4. 移动端自适应，段落行距、文字边距符合微信官方人体工学阅读体验。
"""

import re
import markdown
from typing import Dict, Any


class WeChatFormatter:
    """微信图文专业排版转换器"""

    # 4 大顶尖主题色彩配置
    THEMES: Dict[str, Dict[str, str]] = {
        "think_tank": {
            "name": "🏛️ 权威智库风",
            "primary": "#1a365d",      # 藏青
            "accent": "#881337",       # 勃艮第酒红
            "text_main": "#1e293b",
            "text_sub": "#475569",
            "bg_card": "#f8fafc",
            "border": "#e2e8f0",
            "tag_bg": "#1a365d",
            "tag_text": "#ffffff",
            "highlight": "#1e3a8a",
            "tag_prefix": "PART"
        },
        "defense_tech": {
            "name": "⚡ 硬核防务风",
            "primary": "#0f172a",      # 碳素深黑
            "accent": "#ea580c",       # 战术荧光橙
            "text_main": "#0f172a",
            "text_sub": "#334155",
            "bg_card": "#f1f5f9",
            "border": "#cbd5e1",
            "tag_bg": "#ea580c",
            "tag_text": "#ffffff",
            "highlight": "#c2410c",
            "tag_prefix": "TACTICAL"
        },
        "geopolitics": {
            "name": "🌐 地缘博弈风",
            "primary": "#064e3b",      # 墨绿
            "accent": "#b45309",       # 古铜金
            "text_main": "#1e293b",
            "text_sub": "#475569",
            "bg_card": "#fbfbfb",
            "border": "#e5e7eb",
            "tag_bg": "#064e3b",
            "tag_text": "#fef3c7",
            "highlight": "#047857",
            "tag_prefix": "INSIGHT"
        },
        "breaking": {
            "name": "🚨 战地特稿风",
            "primary": "#991b1b",      # 赤红警报
            "accent": "#18181b",       # 纯墨黑
            "text_main": "#18181b",
            "text_sub": "#3f3f46",
            "bg_card": "#fef2f2",
            "border": "#fecaca",
            "tag_bg": "#991b1b",
            "tag_text": "#ffffff",
            "highlight": "#b91c1c",
            "tag_prefix": "BREAKING"
        }
    }

    @classmethod
    def get_theme(cls, theme_key: str) -> Dict[str, str]:
        return cls.THEMES.get(theme_key, cls.THEMES["think_tank"])

    @classmethod
    def _parse_custom_components(cls, md_text: str, theme: Dict[str, str]) -> str:
        """
        解析并替换自定义富文本组件标签为特定 HTML
        1. :::quote-card [author] ... :::
        2. :::timeline ... :::
        3. :::vs-card [阵营A|阵营B] ... :::
        4. :::spec-grid ... :::
        5. :::insight-box [标题] ... :::
        """
        # 1. 金句卡 :::quote-card [author]
        def render_quote_card(match):
            author = match.group(1) or "战略研判"
            content = match.group(2).strip()
            return f"""
            <section style="margin: 28px 0; padding: 22px 20px 18px 22px; background: {theme['bg_card']}; border-left: 4px solid {theme['accent']}; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); position: relative;">
                <div style="font-size: 32px; line-height: 1; color: {theme['accent']}; opacity: 0.35; font-family: Georgia, serif; position: absolute; top: 12px; left: 14px;">“</div>
                <p style="margin: 0 0 10px 0; font-size: 15.5px; line-height: 1.8; color: {theme['text_main']}; font-weight: 500; text-align: justify; padding-left: 14px;">{content}</p>
                <div style="text-align: right; font-size: 13px; color: {theme['text_sub']}; font-weight: 600; padding-top: 6px; border-top: 1px dashed {theme['border']};">
                    —— {author}
                </div>
            </section>
            """
        md_text = re.sub(r':::quote-card(?:\s+\[(.*?)\])?\s*\n(.*?)\n:::', render_quote_card, md_text, flags=re.DOTALL)

        # 2. 武器参数指标网格 :::spec-grid
        # 格式: 每行一个指标，如 "射程 | 2500 km | 具备末端高机动突破"
        def render_spec_grid(match):
            body = match.group(1).strip()
            items = [line.strip() for line in body.split('\n') if line.strip()]
            cards_html = []
            for item in items:
                parts = [p.strip() for p in item.split('|')]
                if len(parts) >= 2:
                    label = parts[0]
                    val = parts[1]
                    desc = parts[2] if len(parts) > 2 else ""
                    cards_html.append(f"""
                    <div style="flex: 1 1 30%; min-width: 90px; background: #ffffff; border: 1px solid {theme['border']}; border-radius: 6px; padding: 12px 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                        <div style="font-size: 11.5px; color: {theme['text_sub']}; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>
                        <div style="font-size: 19px; font-weight: 800; color: {theme['accent']}; margin: 4px 0 2px 0;">{val}</div>
                        {f'<div style="font-size: 11px; color: #64748b;">{desc}</div>' if desc else ''}
                    </div>
                    """)
            return f"""
            <section style="margin: 24px 0; display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between;">
                {''.join(cards_html)}
            </section>
            """
        md_text = re.sub(r':::spec-grid\s*\n(.*?)\n:::', render_spec_grid, md_text, flags=re.DOTALL)

        # 3. 双方力量对抗卡 :::vs-card [蓝方名称|红方名称]
        # 内容分两部分，通过 === 分割
        def render_vs_card(match):
            parties = (match.group(1) or "攻方力量|守方部署").split('|')
            party_a = parties[0].strip()
            party_b = parties[1].strip() if len(parties) > 1 else "防御方"
            content = match.group(2).strip()
            halves = content.split('===')
            left_content = halves[0].strip() if len(halves) > 0 else ""
            right_content = halves[1].strip() if len(halves) > 1 else ""

            return f"""
            <section style="margin: 26px 0; border: 1px solid {theme['border']}; border-radius: 8px; overflow: hidden; background: #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                <div style="background: {theme['primary']}; color: #ffffff; padding: 8px 14px; font-size: 12.5px; font-weight: 700; display: flex; justify-content: space-between; align-items: center; letter-spacing: 0.5px;">
                    <span>⚔️ 双方实力与战术筹码推演</span>
                    <span style="font-size: 11px; background: rgba(255,255,255,0.18); padding: 2px 6px; border-radius: 3px;">红蓝对抗态势</span>
                </div>
                <div style="display: flex; flex-wrap: wrap; border-top: 1px solid {theme['border']};">
                    <div style="flex: 1 1 45%; padding: 14px 16px; background: #f8fafc; border-right: 1px dashed {theme['border']};">
                        <div style="font-size: 13.5px; font-weight: 700; color: #1d4ed8; margin-bottom: 8px;">🔵 {party_a}</div>
                        <div style="font-size: 13px; color: {theme['text_main']}; line-height: 1.7;">{left_content.replace(chr(10), '<br>')}</div>
                    </div>
                    <div style="flex: 1 1 45%; padding: 14px 16px; background: #fff5f5;">
                        <div style="font-size: 13.5px; font-weight: 700; color: #dc2626; margin-bottom: 8px;">🔴 {party_b}</div>
                        <div style="font-size: 13px; color: {theme['text_main']}; line-height: 1.7;">{right_content.replace(chr(10), '<br>')}</div>
                    </div>
                </div>
            </section>
            """
        md_text = re.sub(r':::vs-card(?:\s+\[(.*?)\])?\s*\n(.*?)\n:::', render_vs_card, md_text, flags=re.DOTALL)

        # 4. 战术解密小贴士 :::insight-box [标题]
        def render_insight_box(match):
            title = match.group(1) or "专业研判解析"
            content = match.group(2).strip()
            return f"""
            <section style="margin: 22px 0; padding: 14px 18px; background: {theme['bg_card']}; border: 1px solid {theme['border']}; border-left: 4px solid {theme['primary']}; border-radius: 5px;">
                <div style="font-weight: 700; color: {theme['primary']}; font-size: 13.5px; margin-bottom: 6px; display: flex; align-items: center;">
                    <span style="display:inline-block; margin-right: 6px;">💡</span> {title}
                </div>
                <div style="font-size: 14px; color: {theme['text_sub']}; line-height: 1.75;">{content}</div>
            </section>
            """
        md_text = re.sub(r':::insight-box(?:\s+\[(.*?)\])?\s*\n(.*?)\n:::', render_insight_box, md_text, flags=re.DOTALL)

        # 5. 时序脉络时间轴 :::timeline
        def render_timeline(match):
            body = match.group(1).strip()
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            nodes_html = []
            for line in lines:
                # 匹配 **时间**：内容 或 - 时间：内容
                m = re.match(r'^[-\*]?\s*(?:\*\*(.*?)\*\*|(.*?))[\s:：]+(.*)', line)
                if m:
                    t_str = m.group(1) or m.group(2)
                    c_str = m.group(3)
                else:
                    t_str = "节点"
                    c_str = line
                nodes_html.append(f"""
                <div style="position: relative; padding-left: 24px; margin-bottom: 14px;">
                    <div style="position: absolute; left: 0; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: {theme['accent']}; border: 2px solid #ffffff; box-shadow: 0 0 0 2px {theme['border']};"></div>
                    <div style="font-size: 12.5px; font-weight: 700; color: {theme['primary']};">{t_str}</div>
                    <div style="font-size: 13.5px; color: {theme['text_sub']}; line-height: 1.6; margin-top: 2px;">{c_str}</div>
                </div>
                """)
            return f"""
            <section style="margin: 24px 0 26px 10px; border-left: 2px solid {theme['border']}; padding: 6px 0 2px 0;">
                {''.join(nodes_html)}
            </section>
            """
        md_text = re.sub(r':::timeline\s*\n(.*?)\n:::', render_timeline, md_text, flags=re.DOTALL)

        return md_text

    @classmethod
    def format_to_wechat_html(
        cls,
        markdown_text: str,
        theme_name: str = "think_tank",
        author: str = "局势洞见研判组",
        images: list = None,
        sources: list = None
    ) -> str:
        """
        将标准 Markdown 转换为内联 CSS 样式的微信图文 HTML
        """
        theme = cls.get_theme(theme_name)

        # 1. 提取导读部分
        lead_content = ""
        lead_match = re.search(r'【导读】[\s:：]*(.*?)(?=\n##|\n#|\Z)', markdown_text, re.DOTALL)
        if lead_match:
            lead_content = lead_match.group(1).strip()
            markdown_text = markdown_text.replace(lead_match.group(0), "")

        # 2. 预处理富文本内联组件 (Quote, Timeline, VS-card, Spec-grid, Insight-box)
        processed_md = cls._parse_custom_components(markdown_text, theme)

        # 3. 基础 Markdown 解析
        raw_html = markdown.markdown(
            processed_md,
            extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists']
        )

        # 4. 样式规则装配
        style_container = (
            f"max-width: 677px; margin: 0 auto; padding: 20px 14px; "
            f"font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', "
            f"'Microsoft YaHei', sans-serif; color: {theme['text_main']}; line-height: 1.85; letter-spacing: 0.35px; "
            f"background-color: #ffffff; word-break: break-word;"
        )

        style_lead_box = (
            f"margin: 0 0 28px 0; padding: 18px 20px; background-color: {theme['bg_card']}; "
            f"border-left: 4px solid {theme['primary']}; border-radius: 6px; "
            f"border-top: 1px solid {theme['border']}; border-right: 1px solid {theme['border']}; border-bottom: 1px solid {theme['border']};"
        )

        style_p = f"margin: 0 0 18px 0; font-size: 15.5px; color: {theme['text_main']}; line-height: 1.85; text-align: justify;"
        style_strong = f"color: {theme['highlight']}; font-weight: 700;"
        style_h3 = f"margin: 24px 0 12px 0; font-size: 16px; font-weight: 700; color: {theme['primary']}; border-left: 3.5px solid {theme['accent']}; padding-left: 10px; line-height: 1.4;"
        style_quote = (
            f"margin: 22px 0; padding: 14px 18px; background: {theme['bg_card']}; "
            f"border-left: 4px solid {theme['border']}; border-radius: 4px; "
            f"font-style: normal; color: {theme['text_sub']}; font-size: 14px; line-height: 1.75;"
        )
        style_hr = f"margin: 28px 0; border: 0; border-top: 1px dashed {theme['border']};"

        # 表格强化 (斑马纹与圆角阴影)
        style_table_wrap = "margin: 22px 0; overflow-x: auto; -webkit-overflow-scrolling: touch;"
        style_table = f"width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: left; line-height: 1.5; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.04); border: 1px solid {theme['border']};"
        style_th = f"background-color: {theme['primary']}; color: #f8fafc; font-weight: 700; padding: 10px 12px; border: 1px solid {theme['primary']}; font-size: 12.5px; text-align: center; white-space: nowrap; vertical-align: middle; letter-spacing: 0.3px;"
        style_td = f"padding: 9px 12px; border: 1px solid {theme['border']}; color: {theme['text_main']}; background-color: #ffffff; font-size: 13px; vertical-align: middle; line-height: 1.5;"

        style_ul = f"margin: 0 0 18px 0; padding-left: 20px; color: {theme['text_sub']};"
        style_ol = f"margin: 0 0 18px 0; padding-left: 22px; color: {theme['text_sub']};"
        style_li = "margin-bottom: 8px; font-size: 15px; line-height: 1.75;"

        style_footer = (
            f"margin-top: 40px; padding: 22px 18px; background-color: {theme['bg_card']}; "
            f"border-top: 2px solid {theme['border']}; border-radius: 6px; font-size: 13px; "
            f"color: {theme['text_sub']}; line-height: 1.75; text-align: center;"
        )

        # 5. 注入内联样式：段落 <p> (排除已经在组件内的特殊段落)
        styled_html = re.sub(
            r'<p>(.*?)</p>',
            lambda m: f'<p style="{style_p}">{m.group(1)}</p>' if 'style=' not in m.group(0) else m.group(0),
            raw_html,
            flags=re.DOTALL
        )

        # 6. 注入加粗 <strong>
        styled_html = re.sub(
            r'<strong>(.*?)</strong>',
            lambda m: f'<strong style="{style_strong}">{m.group(1)}</strong>' if 'style=' not in m.group(0) else m.group(0),
            styled_html
        )

        # 7. 二级标题 <h2> (动态应用主题角标与主副标题)
        def replace_h2(match):
            title = match.group(1).strip()
            num_match = re.match(r'^([0-9A-Za-z一二三四五六七八九十]+)[\s、.:](.*)', title)
            tag_prefix = theme["tag_prefix"]
            if num_match:
                tag_num = num_match.group(1)
                text_part = num_match.group(2)
                badge_text = f"{tag_prefix} {tag_num}"
            else:
                badge_text = tag_prefix
                text_part = title

            return (
                f'<section style="display: flex; align-items: center; margin: 34px 0 18px 0; padding-bottom: 8px; border-bottom: 2px solid {theme["border"]};">'
                f'<span style="background: {theme["tag_bg"]}; color: {theme["tag_text"]}; font-size: 11.5px; font-weight: 700; padding: 3px 9px; border-radius: 4px; margin-right: 10px; text-transform: uppercase; letter-spacing: 0.5px;">{badge_text}</span>'
                f'<span style="display: inline-block; font-size: 17.5px; font-weight: 700; color: {theme["primary"]}; letter-spacing: 0.5px;">{text_part}</span>'
                f'</section>'
            )

        styled_html = re.sub(r'<h2>(.*?)</h2>', replace_h2, styled_html)

        # 8. 三级标题 <h3>
        styled_html = re.sub(r'<h3>(.*?)</h3>', lambda m: f'<h3 style="{style_h3}">{m.group(1)}</h3>', styled_html)

        # 9. 引用块 <blockquote>
        styled_html = re.sub(
            r'<blockquote>\s*(?:<p[^>]*>)?(.*?)(?:</p>)?\s*</blockquote>',
            lambda m: f'<blockquote style="{style_quote}">{m.group(1)}</blockquote>',
            styled_html,
            flags=re.DOTALL
        )

        # 10. 表格样式
        styled_html = re.sub(
            r'<table>(.*?)</table>',
            lambda m: f'<section style="{style_table_wrap}"><table style="{style_table}">{m.group(1)}</table></section>',
            styled_html,
            flags=re.DOTALL
        )
        def _replace_th(m):
            # 剥离 <strong> 包裹（前序步骤可能染了深色样式），保持纯净白色表头文字
            raw_content = m.group(2)
            clean_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'\1', raw_content, flags=re.DOTALL)
            return f'<th style="{style_th}">{clean_content}</th>'

        def _replace_td(m):
            return f'<td style="{style_td}">{m.group(2)}</td>'

        styled_html = re.sub(r'<th\b([^>]*)>(.*?)</th>', _replace_th, styled_html, flags=re.DOTALL)
        styled_html = re.sub(r'<td\b([^>]*)>(.*?)</td>', _replace_td, styled_html, flags=re.DOTALL)

        # 11. 列表
        styled_html = re.sub(r'<ul>', f'<ul style="{style_ul}">', styled_html)
        styled_html = re.sub(r'<ol>', f'<ol style="{style_ol}">', styled_html)
        styled_html = re.sub(r'<li>(.*?)</li>', lambda m: f'<li style="{style_li}">{m.group(1)}</li>', styled_html, flags=re.DOTALL)

        # 12. 分割线
        styled_html = re.sub(r'<hr\s*/?>', f'<hr style="{style_hr}" />', styled_html)

        # 12.1 自动注入正文双图 (图一: 现场实录装备大片, 图二: 战术态势示意图)
        if images and len(images) > 0:
            img1 = images[0]
            img1_url = img1.get('url', img1.get('path', ''))
            img1_cap = img1.get('caption', '战区一线装备部署与交锋实录')
            img1_html = f'''
            <section style="margin: 26px auto; text-align: center; max-width: 100%;">
                <div style="border-radius: 6px; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.06); border: 1px solid {theme['border']};">
                    <img src="{img1_url}" style="width: 100%; display: block; margin: 0 auto;" />
                </div>
                <p style="font-size: 12.5px; color: {theme['text_sub']}; margin: 8px 0 0 0; text-align: center; letter-spacing: 0.5px;">
                    ▲ {img1_cap}
                </p>
            </section>
            '''
            # 插入在首个章节结束处
            match_part1 = re.search(r'(<section style="display: flex;.*?</h2>.*?</p>)', styled_html, re.DOTALL)
            if match_part1:
                end_pos = match_part1.end()
                styled_html = styled_html[:end_pos] + img1_html + styled_html[end_pos:]
            else:
                styled_html = img1_html + styled_html

            if len(images) > 1:
                img2 = images[1]
                img2_url = img2.get('url', img2.get('path', ''))
                img2_cap = img2.get('caption', '战术态势推演：关键海域防空雷达盲区与突防弹道示意')
                img2_html = f'''
                <section style="margin: 28px auto; text-align: center; max-width: 100%;">
                    <div style="border-radius: 6px; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.06); border: 1px solid {theme['border']};">
                        <img src="{img2_url}" style="width: 100%; display: block; margin: 0 auto;" />
                    </div>
                    <p style="font-size: 12.5px; color: {theme['text_sub']}; margin: 8px 0 0 0; text-align: center; letter-spacing: 0.5px; font-weight: 500;">
                        ▲ {img2_cap}
                    </p>
                </section>
                '''
                styled_html = styled_html + img2_html

        # 12.2 自动生成真实事实溯源与信源附录
        sources_html = ""
        if sources and len(sources) > 0:
            lis = "".join([f"<li style='margin-bottom: 4px;'>{s}</li>" for s in sources])
            sources_html = f'''
            <section style="margin: 32px 0 16px 0; padding: 14px 18px; background: {theme['bg_card']}; border: 1px solid {theme['border']}; border-left: 3.5px solid {theme['primary']}; border-radius: 6px; font-size: 12px; color: {theme['text_sub']}; line-height: 1.7;">
                <div style="font-weight: 700; color: {theme['primary']}; margin-bottom: 6px; font-size: 12.5px;">
                    📚 事实溯源与权威公开参考信源
                </div>
                <ul style="margin: 0; padding-left: 18px; color: {theme['text_sub']};">
                    {lis}
                </ul>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 6px; border-top: 1px dashed {theme['border']}; padding-top: 5px;">
                    * 声明：本文依据上述公开一手战报与官方通报客观研判，文责自负，仅供交流。
                </div>
            </section>
            '''

        # 13. 组装导读与页尾
        lead_html = ""
        if lead_content:
            lead_html = f"""
            <section style="{style_lead_box}">
                <div style="font-weight: 700; color: {theme['primary']}; margin-bottom: 8px; font-size: 13.5px; letter-spacing: 0.8px; display: flex; align-items: center;">
                    <span style="display:inline-block; width:4px; height:14px; background:{theme['accent']}; margin-right:6px; border-radius:2px;"></span>
                    战略研判要点 · 核心速览
                </div>
                <div style="font-size:14.5px; color:{theme['text_sub']}; line-height:1.75;">{lead_content}</div>
            </section>
            """

        footer_html = f"""
        <section style="{style_footer}">
            <div style="font-weight: 700; color: {theme['primary']}; font-size: 14.5px; margin-bottom: 6px;">
                【{author}】
            </div>
            <div style="color: {theme['text_sub']}; font-size: 13px;">立足 {datetime.datetime.now().year} 全球防务与地缘博弈新常态。不跟风，不站队，只看事实与底层逻辑。</div>
            <div style="font-size: 11.5px; color: #94a3b8; margin-top: 10px; border-top: 1px dashed {theme['border']}; padding-top: 8px;">
                * 声明：本文基于公开防务情报、官方战报与战略兵棋推演客观撰写，文责自负，仅供学术与战略交流。
            </div>
        </section>
        """

        return f"""<section style="{style_container}">{lead_html}{styled_html}{sources_html}{footer_html}</section>"""

    @classmethod
    def format_markdown(cls, markdown_text: str, theme_name: str = "think_tank", author: str = "局势洞见研判组", images: list = None, sources: list = None) -> str:
        """别名与快捷方法"""
        return cls.format_to_wechat_html(markdown_text, theme_name=theme_name, author=author, images=images, sources=sources)
