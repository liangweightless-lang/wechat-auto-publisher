# -*- coding: utf-8 -*-
"""
防务与地缘热点智能爬虫模块
职责：
1. 按照关注关键词（如：红海、曼德海峡、胡塞武装、美军舰艇、无人机战术等）定期抓取最新公开资讯；
2. 执行前置合规过滤与历史发布记录去重，防止重复推送；
3. 输出结构化热点选题，支持一键触发“全自动无人值守发布流水线”。
"""

import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
import urllib3
urllib3.disable_warnings()

from config.settings import settings, logger


class DefenseCrawler:
    """防务与国际热点关键词爬虫调度器"""

    # 默认重点监控的国际防务与地缘关键词
    DEFAULT_KEYWORDS = [
        "红海", "曼德海峡", "胡塞武装", "美军", "沙特", "无人机",
        "防空系统", "航母", "驱逐舰", "地缘博弈", "高超音速", "巡航导弹"
    ]

    HISTORY_FILE = Path(__file__).resolve().parent.parent / "assets" / "crawled_history.json"

    @classmethod
    def load_history(cls) -> set:
        """加载已抓取发布过的文章标题指纹，防止重复推送"""
        if cls.HISTORY_FILE.exists():
            try:
                with open(cls.HISTORY_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    @classmethod
    def save_history(cls, title: str):
        """记录已处理过的主题"""
        history = cls.load_history()
        history.add(title.strip())
        cls.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(list(history), f, ensure_ascii=False, indent=2)

    @classmethod
    def fetch_hot_topics(cls, keywords: List[str] = None, limit: int = 5) -> List[Dict[str, str]]:
        """
        从公开资讯聚合流中按照防务关键词筛选最新热点
        :param keywords: 监控关键词列表
        :param limit: 返回最大热点数量
        :return: 包含 title, url, summary 的热点列表
        """
        if not keywords:
            keywords = cls.DEFAULT_KEYWORDS

        history = cls.load_history()
        candidates = []

        # 数据源 1：新浪公开滚动军事与国际资讯流
        # lid=2509 国际防务财经科技滚动源
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&page=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=12)
            data = resp.json()
            items = data.get("result", {}).get("data", [])

            for it in items:
                title = it.get("title", "").strip()
                intro = it.get("intro", "").strip()
                link = it.get("url", "").strip()

                if not title or title in history:
                    continue

                # 必须命中关注关键词
                hit_kw = [kw for kw in keywords if kw in title or kw in intro]
                if not hit_kw:
                    continue

                # 合规安全审查：严禁涉政违规词
                if any(sk in title or sk in intro for sk in settings.SENSITIVE_KEYWORDS):
                    continue

                candidates.append({
                    "title": title,
                    "url": link,
                    "summary": intro[:120],
                    "matched_keyword": hit_kw[0]
                })

                if len(candidates) >= limit:
                    break

        except Exception as e:
            logger.warning(f"资讯源抓取失败: {e}")

        # 若公开滚动流命中较少，补充精选的高价值战术研判选题
        if not candidates:
            logger.info("未命中实时滚动流，激活智库储备焦点选题...")
            fallback_topics = [
                {
                    "title": "红海战局最新推演：胡塞武装如何运用不对称无人机饱和攻击突破拦截网",
                    "url": "",
                    "summary": "围绕曼德海峡商船与护航编队近期攻防冲突，拆解低成本巡航导弹与察打一体无人机的战术效能比。",
                    "matched_keyword": "红海"
                },
                {
                    "title": "美军航母打击群在红海的持续部署困境与补给链消耗复盘",
                    "url": "",
                    "summary": "分析高强度防空作战对宙斯盾驱逐舰垂直发射系统库存、舰员战备周期的极限施压与后勤瓶颈。",
                    "matched_keyword": "美军"
                },
                {
                    "title": "也门战场防空体系演变：沙特爱国者导弹防御系统面临的饱和打击难题",
                    "url": "",
                    "summary": "从拦截成本比（400万美元爱国者对战数万美元巡飞弹）分析现代防空反导体系的经济战困局。",
                    "matched_keyword": "防空系统"
                }
            ]
            for fb in fallback_topics:
                if fb["title"] not in history:
                    candidates.append(fb)
                    if len(candidates) >= limit:
                        break

        logger.info(f"关键词监控抓取完成，成功筛选出 {len(candidates)} 条高契合度研判热点。")
        return candidates
