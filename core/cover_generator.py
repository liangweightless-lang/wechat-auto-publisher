# -*- coding: utf-8 -*-
"""
微信图文高级多版式封面生成模块
职责：
1. 智能裁切为微信官方大图 2.35:1 比例 (940x400)；
2. 支持 3 种杂志级封面版式（权威特刊版式 / 极简电影大片 / 科技态势战术版）；
3. 注入电影级暗角调色、精致双语大标头与战术坐标水印。
"""

from pathlib import Path
from typing import Optional
from config.settings import logger


class CoverGenerator:
    """文章多版式封面图生成工具"""

    @staticmethod
    def crop_to_wechat_ratio(
        image_path: str,
        title: str = "",
        category: str = "国际防务特刊",
        style: str = "magazine",
        output_path: str = "assets/article_cover.jpg"
    ) -> str:
        """
        将任意高分辨率实景照片裁切为微信官方封面最佳比例 2.35:1 (940 x 400) 并合成杂志级排版
        """
        img_p = Path(image_path)
        if not img_p.exists():
            return ""

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image, ImageEnhance, ImageDraw, ImageFont

            with Image.open(img_p) as im:
                im = im.convert("RGB")
                orig_w, orig_h = im.size

                # 微信官方大图比例 2.35:1
                target_w, target_h = 940, 400
                target_ratio = target_w / target_h
                orig_ratio = orig_w / orig_h

                if orig_ratio > target_ratio:
                    new_w = int(orig_h * target_ratio)
                    left = (orig_w - new_w) // 2
                    im_cropped = im.crop((left, 0, left + new_w, orig_h))
                else:
                    new_h = int(orig_w / target_ratio)
                    top = max(0, (orig_h - new_h) // 3)
                    im_cropped = im.crop((0, top, orig_w, top + new_h))

                im_resized = im_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # 胶片电影级质感增强
                enhancer = ImageEnhance.Contrast(im_resized)
                im_final = enhancer.enhance(1.06)

                draw = ImageDraw.Draw(im_final)

                font_large = None
                font_small = None
                font_candidates = [
                    "/System/Library/Fonts/PingFang.ttc",
                    "/System/Library/Fonts/STHeiti Light.ttc",
                    "/System/Library/Fonts/Hiragino Sans GB.ttc",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                ]
                for fc in font_candidates:
                    if Path(fc).exists():
                        try:
                            font_large = ImageFont.truetype(fc, 24)
                            font_small = ImageFont.truetype(fc, 13)
                            break
                        except Exception:
                            pass

                # 根据版式渲染不同的艺术遮罩与版头
                if style == "magazine":
                    # 权威智库特刊风：底部渐变暗黑蒙层 + 居中或左侧大标 + 金色/藏青副标
                    for y in range(target_h - 130, target_h):
                        alpha = int(210 * ((y - (target_h - 130)) / 130))
                        draw.line([(0, y), (target_w, y)], fill=(10, 15, 30, alpha))

                    # 顶部品牌条
                    draw.rectangle([(0, 0), (target_w, 42)], fill=(15, 23, 42))
                    draw.rectangle([(20, 12), (24, 30)], fill=(234, 88, 12))  # 橙色强调条
                    draw.text((34, 13), f"局势洞见 · {category} // 2026 战略研判报告", fill="#cbd5e1", font=font_small)

                    # 底部标题呈现
                    if title:
                        display_title = title if len(title) <= 28 else title[:28] + "..."
                        draw.text((24, target_h - 85), display_title, fill="#ffffff", font=font_large)
                        draw.text((24, target_h - 45), "GLOBAL DEFENSE & GEOPOLITICAL INTELLIGENCE REPORT", fill="#94a3b8", font=font_small)

                elif style == "tactical":
                    # 战术 HUD 极客风：四角战术准星与科技坐标
                    draw.rectangle([(0, 0), (target_w, 36)], fill=(5, 10, 20))
                    draw.text((20, 10), f"TARGET ACQUIRED // {category} // ACTIVE RADAR LOCK", fill="#38bdf8", font=font_small)
                    # 绘制战术十字
                    draw.line([(target_w - 60, 20), (target_w - 20, 20)], fill="#38bdf8", width=2)
                    draw.line([(target_w - 40, 10), (target_w - 40, 30)], fill="#38bdf8", width=2)

                else:
                    # 极简电影宽幅风
                    draw.rectangle([(0, 0), (target_w, 38)], fill=(12, 17, 29))
                    draw.text((24, 11), f"【局势洞见】{category}", fill="#e2e8f0", font=font_small)

                im_final.save(str(out), "JPEG", quality=95)
                logger.info(f"微信多版式封面生成完成 ({style}): {out}")
                return str(out)

        except Exception as e:
            logger.warning(f"裁切大片封面失败: {e}")
            return str(image_path)

    @classmethod
    def generate_default_cover(
        cls,
        title: str,
        category: str = "国际防务特刊",
        source_photo: str = None,
        style: str = "magazine",
        output_path: str = "assets/article_cover.jpg"
    ) -> str:
        """确保有一张极具视觉冲击力的电影级大片封面"""
        if source_photo and Path(source_photo).exists():
            cover_path = cls.crop_to_wechat_ratio(source_photo, title=title, category=category, style=style, output_path=output_path)
            if cover_path:
                return cover_path

        fallback_photo = Path("assets/flux_illustration.jpg")
        if fallback_photo.exists():
            cover_path = cls.crop_to_wechat_ratio(str(fallback_photo), title=title, category=category, style=style, output_path=output_path)
            if cover_path:
                return cover_path

        return str(fallback_photo) if fallback_photo.exists() else ""
