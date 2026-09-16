# -*- coding: utf-8 -*-
"""
文章配图与视觉生成服务模块
职责：
1. 优先从素材源（PDF 内部原图或网页原文插图）自动抓取提取真实图片；
2. 若配置了 AI 生图能力（通义万相 Wanx / OpenAI 等），根据段落意境生成高清纪实配图；
3. 保底生成具有现代防务雷达、战术坐标与智库态势感的矢量/信息图；
4. 负责调用微信 API 将图片上传至腾讯 CDN，并在 HTML 正文中以内联卡片与专业图注形式优雅插入。
"""

import os
import re
import math
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from config.settings import settings, logger


class ImageService:
    """文章插图全流程调度器"""

    @staticmethod
    def extract_images_from_pdf(pdf_path: str, output_dir: str = "assets/temp_extracted") -> List[str]:
        """
        从 PDF 报告中自动抽取内嵌的高清图表与现场照片
        :return: 提取出的本地图片文件路径列表
        """
        path = Path(pdf_path)
        if not path.exists():
            return []

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        extracted_images = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            img_index = 1
            for page_idx, page in enumerate(reader.pages):
                for img_name, img_file in page.images.items():
                    # 过滤过小的图标或装饰性小图（字节数小于 15KB 的忽略）
                    if len(img_file.data) < 15 * 1024:
                        continue
                    suffix = Path(img_name).suffix or ".jpg"
                    save_path = out_dir / f"pdf_img_p{page_idx+1}_{img_index}{suffix}"
                    with open(save_path, "wb") as f:
                        f.write(img_file.data)
                    extracted_images.append(str(save_path))
                    img_index += 1
                    if len(extracted_images) >= 4:  # 最多抽取 4 张主要图表
                        break
                if len(extracted_images) >= 4:
                    break
        except Exception as e:
            logger.warning(f"从 PDF 抽取图片出现异常: {e}")

        if extracted_images:
            logger.info(f"成功从 PDF 中提取出 {len(extracted_images)} 张原版图表/照片。")
        return extracted_images

    @staticmethod
    def extract_images_from_url(url: str, output_dir: str = "assets/temp_extracted") -> List[str]:
        """
        从参考网页链接中自动抓取正文配图
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        extracted = []

        try:
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=12)
            soup = BeautifulSoup(resp.text, "html.parser")

            img_tags = soup.find_all("img")
            for idx, img in enumerate(img_tags):
                src = img.get("src") or img.get("data-src")
                if not src:
                    continue
                if not src.startswith("http"):
                    continue
                # 排除明显的头像、表情包
                if any(k in src.lower() for k in ["avatar", "icon", "logo", "emoji", "qrcode"]):
                    continue

                try:
                    img_resp = requests.get(src, headers=headers, timeout=10)
                    if len(img_resp.content) > 30 * 1024:  # 大于 30KB
                        file_name = out_dir / f"web_img_{idx+1}.jpg"
                        with open(file_name, "wb") as f:
                            f.write(img_resp.content)
                        extracted.append(str(file_name))
                        if len(extracted) >= 3:
                            break
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"从网页提取图片失败: {e}")

        return extracted

    @staticmethod
    def generate_tactical_infographic(
        title: str,
        label: str = "战略态势研判",
        output_path: str = "assets/tactical_infographic.jpg"
    ) -> str:
        """
        自动合成一张具有深海蓝冷峻雷达感、战术坐标与防务智库质感的态势示意图
        （用于在素材无图片时的专业保底配图）
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = 960, 540  # 16:9 黄金宽屏
            # 采用智库深黑与战术海蓝基调
            img = Image.new("RGB", (width, height), color="#0b1329")
            draw = ImageDraw.Draw(img)

            # 1. 绘制战术雷达网格背景
            cx, cy = width // 2, height // 2
            for r in [80, 160, 240, 320]:
                draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline="#1e293b", width=1)

            # 经纬十字准星线
            draw.line([(0, cy), (width, cy)], fill="#1a365d", width=1)
            draw.line([(cx, 0), (cx, height)], fill="#1a365d", width=1)

            # 45度战术虚线
            for angle in [45, 135, 225, 315]:
                rad = math.radians(angle)
                x = cx + int(340 * math.cos(rad))
                y = cy + int(340 * math.sin(rad))
                draw.line([(cx, cy), (x, y)], fill="#1e293b", width=1)

            # 2. 战术边框与角标
            pad = 28
            draw.rectangle([(pad, pad), (width - pad, height - pad)], outline="#2d3748", width=2)
            # 四个角落的高亮短直角
            cl = 16
            for (x, y) in [(pad, pad), (width - pad, pad), (pad, height - pad), (width - pad, height - pad)]:
                draw.rectangle([(x - 2, y - 2), (x + 2, y + 2)], fill="#3182ce")

            # 3. 绘制文字层
            # 顶部战术标
            draw.text((pad + 20, pad + 20), f"[ TACTICAL SITUATION REPORT ] // {label}", fill="#63b3ed")
            draw.text((width - pad - 180, pad + 20), "STATUS: ACTIVE", fill="#38a169")

            # 尝试加载中文字体
            font_candidates = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ]
            font = None
            for fc in font_candidates:
                if Path(fc).exists():
                    try:
                        font = ImageFont.truetype(fc, 30)
                        break
                    except Exception:
                        pass

            # 中央核心研判标题
            display_title = title if len(title) <= 22 else title[:22] + "..."
            if font:
                draw.text((cx - 240, cy - 20), display_title, font=font, fill="#ffffff")
            else:
                draw.text((cx - 180, cy - 20), "GEO-STRATEGIC MAP", fill="#ffffff")

            # 底部战术刻度
            draw.text((pad + 20, height - pad - 35), "COORDINATES: RED SEA & MANDAB // DEFENSE INSIGHT", fill="#718096")

            img.save(str(out), "JPEG", quality=95)
            logger.info(f"合成战术态势图完成: {out}")
            return str(out)

        except Exception as e:
            logger.warning(f"合成态势图失败: {e}")
            return ""

    @classmethod
    def insert_illustration_to_html(
        cls,
        html_content: str,
        image_cdn_url: str,
        caption: str,
        insert_after_part: str = "PART 01"
    ) -> str:
        """
        将微信 CDN 图片与专业图注，无缝以内联卡片形式插入到指定章节之后
        """
        img_card_html = f"""
        <section style="margin: 26px auto; text-align: center; max-width: 100%;">
            <div style="display: inline-block; width: 100%; border-radius: 4px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #edf2f7;">
                <img src="{image_cdn_url}" style="width: 100%; display: block; margin: 0 auto;" />
            </div>
            <p style="font-size: 12.5px; color: #718096; margin: 8px 0 0 0; text-align: center; letter-spacing: 0.5px;">
                {caption}
            </p>
        </section>
        """

        # 查找章节标记（例如 PART 01 或 PART 02）之后的第一个段落结束点 </p>
        pattern = rf'({insert_after_part}.*?</p>)'
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            end_pos = match.end()
            return html_content[:end_pos] + img_card_html + html_content[end_pos:]

        p_match = re.search(r'</p>', html_content)
        if p_match:
            end_pos = p_match.end()
            return html_content[:end_pos] + img_card_html + html_content[end_pos:]

        return html_content + img_card_html
