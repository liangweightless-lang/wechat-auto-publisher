# -*- coding: utf-8 -*-
"""
多维场景 AI 生图与视觉配图服务模块
职责：
1. 彻底告别千篇一律的死板配图，引入 5 大场景化视觉风格引擎；
2. 装备特写 (Macro) / 指挥全息 (C4ISR) / 卫星态势 (Satellite) / 战地纪实 (Reuters) / 特刊图解 (Infographic)；
3. 智能构建高质量 Prompt，调用 SiliconFlow 高质量生图接口；
4. 优雅降级与本地战术图合成能力。
"""

import os
import re
import requests
from pathlib import Path
from typing import Optional, List, Dict
from config.settings import logger

SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/images/generations"


class ImageService:
    """多维视觉与 AI 生图服务"""

    # 5 大专业防务与地缘视觉风格模板
    VISUAL_STYLES: Dict[str, Dict[str, str]] = {
        "photojournalism": {
            "name": "📸 战地纪实特写 (Photojournalism)",
            "suffix": "真实战地新闻纪实摄影，35mm电影胶片质感，真实自然晨光与硝烟，路透社/普利策新闻大奖风格，景深层次分明，8k极高清晰度，冷峻逼真，真实历史感"
        },
        "tactical_macro": {
            "name": "🔍 装备精密微距 (Macro Details)",
            "suffix": "战术装备精密特写，微距工业摄影，机身吸波隐身涂层与铆钉接缝，雷达光电转塔反光，冷灰高强度钛合金质感，工业精密美学，8k超高分辨率"
        },
        "c4isr_command": {
            "name": "🖥️ 联合指挥全息 (C4ISR Center)",
            "suffix": "现代化多域战联合指挥中心，超大弧形全息电子沙盘态势屏，幽蓝与战术橙色冷光，参谋军官专注背影，高科技国防实验室推演氛围，赛博智库质感，8k"
        },
        "satellite_recon": {
            "name": "🛰️ 卫星遥感侦察 (Satellite Recon)",
            "suffix": "军用高分辨率对地观测卫星正射俯瞰视角，合成孔径雷达(SAR)与红外热成像交织伪彩，战术地貌与沿海要塞，地理空间坐标网格覆盖，真实侦察情报大片"
        },
        "infographic": {
            "name": "📊 智库特刊大图 (Think Tank Poster)",
            "suffix": "兰德智库防务特刊主视觉封面，极简杂志风构图，沉稳藏青与双色调对比，战略推演图解，严谨高级视觉传达"
        }
    }

    @classmethod
    def enhance_prompt(cls, raw_prompt: str, style_key: str = "photojournalism") -> str:
        """根据风格模式合成专业分镜头提示词"""
        style = cls.VISUAL_STYLES.get(style_key, cls.VISUAL_STYLES["photojournalism"])
        # 去除用户 prompt 中的重复噪点
        clean_prompt = re.sub(r'[,，\s]*(8k|高清|超清|大片|真实).*', '', raw_prompt).strip()
        return f"{clean_prompt}，{style['suffix']}"

    @classmethod
    def generate_image_by_flux(
        cls,
        prompt: str,
        style_key: str = "photojournalism",
        output_path: str = "assets/flux_illustration.jpg"
    ) -> Optional[str]:
        """
        调用 SiliconFlow 图像大模型生成场景配图
        """
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            logger.warning("未检测到 SILICONFLOW_API_KEY，将启用保底态势图生成机制")
            return cls.generate_tactical_infographic(prompt[:25], output_path=output_path)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        enhanced_prompt = cls.enhance_prompt(prompt, style_key)
        logger.info(f"🎨 正在调用 AI 视觉引擎 [{style_key}] 生成配图: {enhanced_prompt[:40]}...")

        payload = {
            "model": "Kwai-Kolors/Kolors",
            "prompt": enhanced_prompt,
            "image_size": "1024x1024",
            "batch_size": 1
        }

        try:
            resp = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=45)
            data = resp.json()
            if "images" in data and len(data["images"]) > 0:
                img_url = data["images"][0]["url"]
                img_resp = requests.get(img_url, timeout=25)
                with open(out, "wb") as f:
                    f.write(img_resp.content)
                logger.info(f"🎉 场景配图生成成功: {out}")
                return str(out)
            else:
                logger.warning(f"生图返回异常: {data}")
        except Exception as e:
            logger.warning(f"调用 AI 出图失败: {e}")

        # 出错时降级为战术图
        return cls.generate_tactical_infographic(prompt[:25], output_path=output_path)

    @staticmethod
    def generate_tactical_infographic(
        title: str,
        label: str = None,
        output_path: str = "assets/tactical_infographic.jpg"
    ) -> str:
        """保底生成专业科技战术态势图"""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = 960, 540
            img = Image.new("RGB", (width, height), color="#080f1e")
            draw = ImageDraw.Draw(img)

            cx, cy = width // 2, height // 2
            # 战术同心圆雷达波
            for r in [70, 150, 230, 310]:
                draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline="#162238", width=1)

            draw.line([(0, cy), (width, cy)], fill="#1e293b", width=1)
            draw.line([(cx, 0), (cx, height)], fill="#1e293b", width=1)

            pad = 24
            draw.rectangle([(pad, pad), (width - pad, height - pad)], outline="#334155", width=2)
            # 战术四角
            for (x, y) in [(pad, pad), (width - pad, pad), (pad, height - pad), (width - pad, height - pad)]:
                draw.rectangle([(x - 2, y - 2), (x + 2, y + 2)], fill="#ea580c")

            draw.text((pad + 18, pad + 16), f"[ SITUATION REPORT ] // {label}", fill="#38bdf8")
            draw.text((width - pad - 190, pad + 16), f"SYSTEM: {datetime.datetime.now().year} ACTIVE", fill="#22c55e")

            font_candidates = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ]
            font = None
            for fc in font_candidates:
                if Path(fc).exists():
                    try:
                        font = ImageFont.truetype(fc, 28)
                        break
                    except Exception:
                        pass

            display_title = title if len(title) <= 22 else title[:22] + "..."
            if font:
                draw.text((cx - 230, cy - 18), display_title, font=font, fill="#f8fafc")
            else:
                draw.text((cx - 160, cy - 18), "DEFENSE INSIGHT", fill="#f8fafc")

            draw.text((pad + 18, height - pad - 30), "COORDINATES: GLOBAL THEATER // INTELLIGENCE MATRIX", fill="#64748b")
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
        """以内联卡片与专业图注形式插入到微信 HTML"""
        img_card_html = f"""
        <section style="margin: 26px auto; text-align: center; max-width: 100%;">
            <div style="display: inline-block; width: 100%; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
                <img src="{image_cdn_url}" style="width: 100%; display: block; margin: 0 auto;" />
            </div>
            <p style="font-size: 12.5px; color: #64748b; margin: 8px 0 0 0; text-align: center; letter-spacing: 0.5px;">
                ▲ {caption}
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
