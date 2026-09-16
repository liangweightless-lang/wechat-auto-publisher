# -*- coding: utf-8 -*-
"""
微信图文封面生成模块
职责：
1. 优先将 AI 生成的好莱坞电影级战场实景照片，智能裁切为微信官方 2.35:1 (900x383) 黄金大图比例；
2. 注入电影级暗角与智库微标，打造极具视觉冲击力的大片封面。
"""

from pathlib import Path
from config.settings import logger


class CoverGenerator:
    """文章封面图生成工具"""

    @staticmethod
    def crop_to_wechat_ratio(image_path: str, output_path: str = "assets/article_cover.jpg") -> str:
        """
        将任意高分辨率实景照片裁切为微信官方封面最佳比例 2.35:1 (900 x 383)
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

                # 目标微信官方大图比例 2.35:1
                target_w, target_h = 940, 400
                target_ratio = target_w / target_h
                orig_ratio = orig_w / orig_h

                if orig_ratio > target_ratio:
                    # 原图太宽，按高度裁剪两边
                    new_w = int(orig_h * target_ratio)
                    left = (orig_w - new_w) // 2
                    im_cropped = im.crop((left, 0, left + new_w, orig_h))
                else:
                    # 原图太高，居中偏上裁剪
                    new_h = int(orig_w / target_ratio)
                    top = max(0, (orig_h - new_h) // 3)  # 居中偏上，保留焦点
                    im_cropped = im.crop((0, top, orig_w, top + new_h))

                im_resized = im_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # 电影感微调：适度增加对比度，打造冷色调胶片质感
                enhancer = ImageEnhance.Contrast(im_resized)
                im_final = enhancer.enhance(1.08)

                # 在左上角打上精美极简角标：局势洞见
                draw = ImageDraw.Draw(im_final)
                # 绘制半透明黑色渐变遮罩保护顶部文字
                draw.rectangle([(0, 0), (target_w, 48)], fill=(10, 15, 28))
                draw.text((24, 14), "【局势洞见】前沿战术与防务深研", fill="#e2e8f0")

                im_final.save(str(out), "JPEG", quality=95)
                logger.info(f"🎉 微信电影级大片封面裁切完成: {out}")
                return str(out)

        except Exception as e:
            logger.warning(f"裁切大片封面失败: {e}")
            return str(image_path)

    @classmethod
    def generate_default_cover(cls, title: str, source_photo: str = None, output_path: str = "assets/default_cover.jpg") -> str:
        """
        确保有一张极具视觉冲击力的电影级大片封面
        """
        # 如果有现成的实景大片照片，直接裁切为微信封面
        if source_photo and Path(source_photo).exists():
            cover_path = cls.crop_to_wechat_ratio(source_photo, output_path)
            if cover_path:
                return cover_path

        # 尝试检查之前生成的战场照片
        fallback_photo = Path("assets/flux_illustration.jpg")
        if fallback_photo.exists():
            cover_path = cls.crop_to_wechat_ratio(str(fallback_photo), output_path)
            if cover_path:
                return cover_path

        return str(fallback_photo) if fallback_photo.exists() else ""
