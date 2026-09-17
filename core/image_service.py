# -*- coding: utf-8 -*-
"""
微信公众号专业视觉与场景出图引擎 (Visual & Geopolitical Map Service)
特性：
1. 修复 API 密钥统一取用 settings.LLM_API_KEY，模型采用已验证稳定的 Tongyi-MAI/Z-Image-Turbo 与 Kwai-Kolors；
2. 智能识别新闻涉及的核心地缘战区（红海/波斯湾/南海/台海/东欧黑海/半岛），生成真实地缘态势地图照片；
3. 多级保底：AI 实时地理测绘出图 -> 本地高清战区地图库 -> 战术制图雷达图，保证 100% 稳定出图。
"""

import os
import re
import time
import requests
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from config.settings import settings, logger

BASE_DIR = Path(__file__).resolve().parent.parent
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/images/generations"


class ImageService:
    """防务与地缘长文视觉大片与地缘战区地图生成引擎"""

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

    # 地缘战区模式与图注规则表
    GEOPOLITICAL_REGIONS = [
        {
            "keys": ["红海", "曼德海峡", "也门", "胡塞", "亚丁湾", "苏伊士"],
            "region": "红海与曼德海峡关键咽喉水道",
            "prompt_region": "Red Sea and Bab-el-Mandeb Strait, Yemen coastline and naval shipping corridors",
            "caption": "▲ 地缘态势地图：红海曼德海峡与也门沿岸关键航道封控与突防预警示意",
            "fallback_file": "assets/maps/red_sea_map.jpg"
        },
        {
            "keys": ["波斯湾", "霍尔木兹", "伊朗", "沙特", "以色列", "以军", "加沙", "哈马斯", "真主党", "中东"],
            "region": "中东波斯湾与霍尔木兹海峡战略走廊",
            "prompt_region": "Middle East Persian Gulf, Strait of Hormuz, Iran and regional strategic airspaces",
            "caption": "▲ 地缘态势地图：中东核心战区与波斯湾战略走廊要塞部署态势",
            "fallback_file": "assets/maps/middle_east_map.jpg"
        },
        {
            "keys": ["南海", "仁爱礁", "黄岩岛", "菲律宾", "台海", "台湾海峡", "第一岛链", "巴士海峡"],
            "region": "南海海域与台湾海峡战略通道",
            "prompt_region": "South China Sea and Taiwan Strait, First Island Chain shipping lanes and naval chokepoints",
            "caption": "▲ 地缘态势地图：南海关键航道与第一岛链海空前哨防御纵深示意",
            "fallback_file": "assets/maps/south_china_sea_map.jpg"
        },
        {
            "keys": ["乌克兰", "俄军", "顿巴斯", "黑海", "克里米亚", "北约", "波罗的海", "库尔斯克"],
            "region": "东欧战区与黑海战略出海口",
            "prompt_region": "Eastern Europe, Black Sea basin, Crimea and strategic defense buffer zones",
            "caption": "▲ 地缘态势地图：东欧黑海沿岸关键海空通道与战略交锋接触线示意",
            "fallback_file": "assets/maps/eastern_europe_map.jpg"
        },
        {
            "keys": ["朝鲜", "半岛", "三八线", "日本海", "朝韩"],
            "region": "东北亚与朝鲜半岛前沿态势",
            "prompt_region": "Korean Peninsula, 38th parallel DMZ and Sea of Japan maritime zone",
            "caption": "▲ 地缘态势地图：东北亚与半岛军事分界线海空战术态势示意",
            "fallback_file": "assets/maps/red_sea_map.jpg"
        }
    ]

    @classmethod
    def _get_api_key(cls) -> str:
        """获取有效的 SiliconFlow API Key"""
        return os.getenv("SILICONFLOW_API_KEY") or settings.LLM_API_KEY or ""

    @classmethod
    def detect_region_and_caption(cls, title: str, content: str = "") -> Dict[str, str]:
        """智能探测文章涉及的核心地缘地理战区与配套专业图注"""
        text = (title + " " + content).lower()
        for reg in cls.GEOPOLITICAL_REGIONS:
            if any(k.lower() in text for k in reg["keys"]):
                return reg
        return {
            "region": "全球地缘博弈核心咽喉水道",
            "prompt_region": "Global strategic geopolitical chokepoint and maritime shipping corridor",
            "caption": "▲ 地缘态势地图：全球战略走廊与核心海空咽喉部署态势示意",
            "fallback_file": "assets/maps/red_sea_map.jpg"
        }

    @classmethod
    def enhance_prompt(cls, raw_prompt: str, style_key: str = "photojournalism") -> str:
        """根据风格模式合成专业分镜头提示词"""
        style = cls.VISUAL_STYLES.get(style_key, cls.VISUAL_STYLES["photojournalism"])
        clean_prompt = re.sub(r'[,，\s]*(8k|高清|超清|大片|真实).*', '', raw_prompt).strip()
        return f"{clean_prompt}，{style['suffix']}"

    @classmethod
    def generate_image_by_flux(
        cls,
        prompt: str,
        style_key: str = "photojournalism",
        output_path: str = "assets/flux_illustration.jpg"
    ) -> Optional[str]:
        """调用 SiliconFlow 图像大模型生成场景纪实大片"""
        api_key = cls._get_api_key()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if not api_key:
            logger.warning("未检测到有效生图 API Key，启用战术态势底图机制")
            return cls.generate_tactical_infographic(prompt[:25], output_path=output_path)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        enhanced_prompt = cls.enhance_prompt(prompt, style_key)
        logger.info(f"🎨 调用 AI 视觉引擎生成配图: {enhanced_prompt[:40]}...")

        # 优先使用实测稳定的极速模型 Tongyi-MAI/Z-Image-Turbo，备选 Kwai-Kolors/Kolors
        candidate_models = ["Tongyi-MAI/Z-Image-Turbo", "Kwai-Kolors/Kolors"]

        for model in candidate_models:
            payload = {
                "model": model,
                "prompt": enhanced_prompt,
                "image_size": "1024x576"
            }
            try:
                resp = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=25)
                data = resp.json()
                if "images" in data and len(data["images"]) > 0:
                    img_url = data["images"][0]["url"]
                    img_resp = requests.get(img_url, timeout=20)
                    with open(out, "wb") as f:
                        f.write(img_resp.content)
                    logger.info(f"🎉 场景配图生成成功 [{model}]: {out}")
                    return str(out)
                else:
                    logger.warning(f"模型 {model} 返回异常: {data.get('message') or data}")
            except Exception as e:
                logger.warning(f"模型 {model} 请求失败: {e}")

        # 出错时降级为本地战术图
        return cls.generate_tactical_infographic(prompt[:25], output_path=output_path)

    @classmethod
    def generate_geopolitical_map(
        cls,
        title: str,
        content: str = "",
        output_path: str = "assets/tactical_situation.jpg"
    ) -> Tuple[str, str]:
        """
        根据新闻涉及的地理战区，智能生成或匹配真实地缘战区态势地图照片
        返回: (图片本地路径, 专业图注)
        """
        reg_info = cls.detect_region_and_caption(title, content)
        caption = reg_info["caption"]
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        api_key = cls._get_api_key()
        if api_key:
            map_prompt = (
                f"专业地缘战略态势地图与战术地理测绘大片，标注 {reg_info['region']}，"
                f"清晰呈现关键海上航道、防空识别区与战略纵深要地，正射卫星俯瞰视角，"
                f"真实地理测绘标尺与经纬度线，8k超高清制图学大片，权威地缘期刊风格"
            )
            logger.info(f"🗺️ 正在为新闻生成专属地缘态势地图: {reg_info['region']}...")
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "Tongyi-MAI/Z-Image-Turbo",
                    "prompt": map_prompt,
                    "image_size": "1024x576"
                }
                resp = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=20)
                data = resp.json()
                if "images" in data and len(data["images"]) > 0:
                    img_url = data["images"][0]["url"]
                    img_resp = requests.get(img_url, timeout=15)
                    with open(out, "wb") as f:
                        f.write(img_resp.content)
                    logger.info(f"🎉 地缘态势地图生成成功: {out}")
                    return str(out), caption
            except Exception as e:
                logger.warning(f"AI 地图在线生成失败，启用本地高清地缘底图: {e}")

        # 降级 1: 若本地已存在该区域的高清战区地图，直接复制使用
        fallback_path = BASE_DIR / reg_info["fallback_file"]
        if fallback_path.exists():
            try:
                import shutil
                shutil.copyfile(str(fallback_path), str(out))
                logger.info(f"🗺️ 成功加载本地战区地图底图: {fallback_path}")
                return str(out), caption
            except Exception as e:
                logger.warning(f"复制底图异常: {e}")

        # 降级 2: 动态绘制专业战术雷达地图
        cls.generate_tactical_infographic(
            title=reg_info["region"],
            label="GEOPOLITICAL SITUATION REPORT",
            output_path=str(out)
        )
        return str(out), caption

    @staticmethod
    def generate_tactical_infographic(
        title: str,
        label: str = "STRATEGIC SITUATION REPORT",
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
            for (x, y) in [(pad, pad), (width - pad, pad), (pad, height - pad), (width - pad, height - pad)]:
                draw.rectangle([(x - 2, y - 2), (x + 2, y + 2)], fill="#ea580c")

            safe_label = label or "DEFENSE SITUATION"
            draw.text((pad + 18, pad + 16), f"[ {safe_label} ]", fill="#38bdf8")
            draw.text((width - pad - 190, pad + 16), f"STATUS: {datetime.datetime.now().year} ACTIVE", fill="#22c55e")

            font_candidates = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ]
            font = None
            for fc in font_candidates:
                if Path(fc).exists():
                    try:
                        font = ImageFont.truetype(fc, 26)
                        break
                    except Exception:
                        pass

            display_title = title if len(title) <= 24 else title[:24] + "..."
            if font:
                draw.text((cx - 210, cy - 16), display_title, font=font, fill="#f8fafc")
            else:
                draw.text((cx - 150, cy - 16), "GEOPOLITICAL THEATER", fill="#f8fafc")

            draw.text((pad + 18, height - pad - 28), "COORDINATES: STRATEGIC MARITIME PASSAGE // THEATER SATELLITE", fill="#64748b")
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
