# -*- coding: utf-8 -*-
"""
文章配图与视觉生成服务模块
职责：
1. 优先从素材源（PDF 内部原图或网页原文插图）自动抓取提取真实图片；
2. 接入 SiliconFlow FLUX.1 / SD 等顶级文生图模型，根据文章战况自动生成好莱坞大片级军事纪实插图；
3. 保底生成具有现代防务雷达、战术坐标与智库态势感的矢量图；
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
    def generate_ai_flux_image(prompt: str, output_path: str = "assets/flux_illustration.jpg") -> Optional[str]:
        """
        调用 SiliconFlow Kwai-Kolors/Kolors 顶级文生图模型生成电影级写实插图
        """
        api_key = settings.LLM_API_KEY
        if not api_key:
            return None

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        url = "https://api.siliconflow.cn/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 增强提示词，注入冷色调军事新闻纪实摄影质感
        enhanced_prompt = f"{prompt}，军事纪实摄影，冷色调，超高清，8k细节，真实大片质感"

        payload = {
            "model": "Kwai-Kolors/Kolors",
            "prompt": enhanced_prompt,
            "image_size": "1024x1024",
            "batch_size": 1
        }

        logger.info(f"正在调用 Kolors 生成电影级战场配图: {prompt[:30]}...")
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            data = resp.json()
            if "images" in data and len(data["images"]) > 0:
                img_url = data["images"][0]["url"]
                img_resp = requests.get(img_url, timeout=25)
                with open(out, "wb") as f:
                    f.write(img_resp.content)
                logger.info(f"🎉 电影级战场配图生成成功: {out}")
                return str(out)
            else:
                logger.warning(f"生图返回信息: {data}")
        except Exception as e:
            logger.warning(f"调用 AI 出图失败: {e}")

        return None

    @staticmethod
    def extract_images_from_pdf(pdf_path: str, output_dir: str = "assets/temp_extracted") -> List[str]:
        """从 PDF 报告中自动抽取内嵌的高清图表与现场照片"""
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
                    if len(img_file.data) < 15 * 1024:
                        continue
                    suffix = Path(img_name).suffix or ".jpg"
                    save_path = out_dir / f"pdf_img_p{page_idx+1}_{img_index}{suffix}"
                    with open(save_path, "wb") as f:
                        f.write(img_file.data)
                    extracted_images.append(str(save_path))
                    img_index += 1
                    if len(extracted_images) >= 3:
                        break
                if len(extracted_images) >= 3:
                    break
        except Exception as e:
            logger.warning(f"从 PDF 抽取图片出现异常: {e}")

        return extracted_images

    @staticmethod
    def extract_images_from_url(url: str, output_dir: str = "assets/temp_extracted") -> List[str]:
        """从参考网页链接中自动抓取正文配图"""
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
                if not src or not src.startswith("http"):
                    continue
                if any(k in src.lower() for k in ["avatar", "icon", "logo", "emoji", "qrcode"]):
                    continue

                try:
                    img_resp = requests.get(src, headers=headers, timeout=10)
                    if len(img_resp.content) > 30 * 1024:
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
        """自动合成保底战术态势图"""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = 960, 540
            img = Image.new("RGB", (width, height), color="#0b1329")
            draw = ImageDraw.Draw(img)

            cx, cy = width // 2, height // 2
            for r in [80, 160, 240, 320]:
                draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline="#1e293b", width=1)

            draw.line([(0, cy), (width, cy)], fill="#1a365d", width=1)
            draw.line([(cx, 0), (cx, height)], fill="#1a365d", width=1)

            pad = 28
            draw.rectangle([(pad, pad), (width - pad, height - pad)], outline="#2d3748", width=2)
            for (x, y) in [(pad, pad), (width - pad, pad), (pad, height - pad), (width - pad, height - pad)]:
                draw.rectangle([(x - 2, y - 2), (x + 2, y + 2)], fill="#3182ce")

            draw.text((pad + 20, pad + 20), f"[ TACTICAL SITUATION REPORT ] // {label}", fill="#63b3ed")
            draw.text((width - pad - 180, pad + 20), "STATUS: ACTIVE", fill="#38a169")

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

            display_title = title if len(title) <= 22 else title[:22] + "..."
            if font:
                draw.text((cx - 240, cy - 20), display_title, font=font, fill="#ffffff")
            else:
                draw.text((cx - 180, cy - 20), "GEO-STRATEGIC MAP", fill="#ffffff")

            draw.text((pad + 20, height - pad - 35), "COORDINATES: RED SEA & MIDDLE EAST // DEFENSE INSIGHT", fill="#718096")
            img.save(str(out), "JPEG", quality=95)
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
        """以内联卡片与专业图注形式插入到指定章节之后"""
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
