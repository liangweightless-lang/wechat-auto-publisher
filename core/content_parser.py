# -*- coding: utf-8 -*-
"""
多源素材解析模块
职责：支持从本地 PDF 智库报告、纯文本/Markdown 文件或网页长文链接中抽取干净的正文内容与核心数据。
"""

from pathlib import Path
from typing import Optional
from config.settings import logger


class ContentParser:
    """素材解析与文本提取工具集"""

    @staticmethod
    def extract_from_pdf(pdf_path: str, max_pages: int = 30) -> str:
        """
        从 PDF 舆情/智库报告中提取文字内容
        :param pdf_path: PDF 文件路径
        :param max_pages: 最大提取页数（防止超长耗尽上下文）
        :return: 结构化纯文本
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"未找到指定的 PDF 文件: {pdf_path}")

        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("未安装 pypdf 依赖，请先运行: pip install pypdf")

        logger.info(f"正在解析 PDF 报告: {path.name} ...")
        reader = PdfReader(str(path))
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)

        text_blocks = []
        for i in range(pages_to_read):
            page = reader.pages[i]
            page_text = page.extract_text() or ""
            # 去除首尾空白，并追加页码标记
            cleaned = page_text.strip()
            if cleaned:
                text_blocks.append(f"--- 第 {i+1} 页 ---\n{cleaned}")

        full_content = "\n\n".join(text_blocks)
        logger.info(f"PDF 解析完成，共读取 {pages_to_read}/{total_pages} 页，提取约 {len(full_content)} 字符。")
        return full_content

    @staticmethod
    def extract_from_text_file(file_path: str) -> str:
        """从本地 txt 或 md 文件读取文本"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
        logger.info(f"成功读取本地文本文件: {path.name} ({len(content)} 字符)")
        return content

    @staticmethod
    def extract_from_url(url: str) -> str:
        """
        从网页链接（如防务新闻、公众号文章网页版）中提取核心正文
        """
        logger.info(f"正在从网页提取内容: {url} ...")
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, include_formatting=False, include_links=False)
                if result:
                    logger.info(f"网页正文提取成功，提取约 {len(result)} 字符")
                    return result
        except Exception as e:
            logger.warning(f"使用 trafilatura 提取网页失败: {e}，尝试简易 requests 备选...")

        # 备选方案：简易 requests + BeautifulSoup
        import requests
        from bs4 import BeautifulSoup

        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")

        # 移除无用标签
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 20]
        content = "\n\n".join(paragraphs)
        logger.info(f"备选方案提取完成，共 {len(paragraphs)} 个段落。")
        return content
