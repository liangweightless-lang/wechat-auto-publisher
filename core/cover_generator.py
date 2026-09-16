# -*- coding: utf-8 -*-
"""
微信图文封面生成模块
职责：在未提供指定封面时，自动生成一张符合微信最佳比例 (2.35:1) 的极简深海蓝智库质感封面图。
"""

from pathlib import Path
from config.settings import logger


class CoverGenerator:
    """文章封面图生成工具"""

    @staticmethod
    def generate_default_cover(title: str, output_path: str = "assets/default_cover.jpg") -> str:
        """
        生成或确保有一张可用的封面图 (900x383 像素，微信 2.35:1 官方比例)
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image, ImageDraw, ImageFont

            # 微信官方大图比例 2.35:1 (推荐 900 x 383)
            width, height = 900, 383
            # 深海冷黑质感底色
            image = Image.new("RGB", (width, height), color="#14213d")
            draw = ImageDraw.Draw(image)

            # 绘制极简科技边框装饰线
            draw.rectangle([(20, 20), (width - 20, height - 20)], outline="#2a4365", width=2)
            draw.rectangle([(24, 24), (width - 24, height - 24)], outline="#1e293b", width=1)

            # 左上角标识
            draw.text((40, 40), "局势洞见 | 深度观察", fill="#90cdf4")

            # 绘制中心主标题（若有中文字体则绘制，无中文字体则绘制几何高质感装饰）
            # 尝试在 macOS / Linux 上寻找标准字体
            font_candidates = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
            ]
            font = None
            for fc in font_candidates:
                if Path(fc).exists():
                    try:
                        font = ImageFont.truetype(fc, 36)
                        break
                    except Exception:
                        pass

            if font:
                # 简单截断换行
                display_title = title if len(title) <= 18 else title[:18] + "..."
                draw.text((40, 160), display_title, font=font, fill="#ffffff")
            else:
                draw.text((40, 160), "STRATEGIC INSIGHT", fill="#ffffff")

            image.save(str(out), "JPEG", quality=95)
            logger.info(f"封面图生成成功: {out}")
            return str(out)

        except ImportError:
            logger.warning("Pillow 未安装，生成简易占位图片...")
            # 纯色最小 JPEG 二进制占位
            # 1x1 像素纯色 jpeg 基础字节
            raw_jpeg = bytes.fromhex(
                "ffd8ffe000104a46494600010101004800480000ffdb004300080606070605080707070909"
                "080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30"
                "323434341f27393d38323c2e333431ffc0000b080001000101011100ffc4001f0000010501"
                "010101010100000000000000000102030405060708090a0bffda0008010100003f007f00ff"
                "d9"
            )
            with open(out, "wb") as f:
                f.write(raw_jpeg)
            return str(out)
