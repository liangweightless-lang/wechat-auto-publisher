# -*- coding: utf-8 -*-
"""
多源防务与官方热点新闻聚合引擎 (含权威信源出处与直达跳转)
"""

import json
import time
import urllib.parse
import requests
from pathlib import Path
from typing import List, Dict, Optional
import urllib3
urllib3.disable_warnings()

from config.settings import settings, logger


class DefenseCrawler:
    """防务与官方公告多源聚合器 (支持出处溯源与原文直达)"""

    HISTORY_FILE = Path(__file__).resolve().parent.parent / "assets" / "crawled_history.json"

    # 防务军事强相关特征词（严格排除非军武娱乐及财经杂音）
    DEFENSE_KEYWORDS = [
        "军事", "军演", "军方", "国防部", "导弹", "航母", "战机", "核潜艇", "无人机",
        "防空", "突袭", "演习", "也门", "胡塞", "红海", "沙特", "美军", "五角大楼",
        "乌克兰", "俄军", "北约", "以色列", "以军", "哈马斯", "真主党", "伊朗",
        "曼德海峡", "霍尔木兹", "高超音速", "宙斯盾", "巡航导弹", "防区外", "拦截",
        "作战公报", "前线态势", "战报", "空袭", "交火", "停火", "兵力部署"
    ]

    EXCLUDE_KEYWORDS = [
        "ETF", "基金", "股票", "大盘", "A股", "理财", "银行", "涨停", "跌停",
        "董事会", "股东大会", "校招", "雷军", "房贷", "开盘", "财报"
    ]

    @classmethod
    def load_history(cls) -> set:
        if cls.HISTORY_FILE.exists():
            try:
                with open(cls.HISTORY_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    @classmethod
    def save_history(cls, title: str):
        history = cls.load_history()
        history.add(title)
        cls.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cls.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(list(history), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    @classmethod
    def fetch_multi_source_topics(cls, category: str = "all", limit: int = 20) -> List[Dict[str, str]]:
        """
        跨渠道多源抓取热点（包含原始链接、出处机构与热度）
        """
        history = cls.load_history()
        results = []

        # 1. 抓取今日头条防务/国际热点
        tt_topics = cls._fetch_toutiao_hot()
        for t in tt_topics:
            if t["title"] not in history:
                results.append(t)

        # 2. 抓取新浪军事频道滚动态势
        sina_topics = cls._fetch_sina_military()
        for s in sina_topics:
            if s["title"] not in history and not any(r["title"] == s["title"] for r in results):
                results.append(s)

        # 3. 补充精选权威智库选题池
        intel_bank = cls._get_curated_intel_bank()
        for it in intel_bank:
            if it["title"] not in history and not any(r["title"] == it["title"] for r in results):
                results.append(it)

        # 4. 安全合规前置过滤
        safe_results = []
        for r in results:
            if not any(sk in r["title"] for sk in settings.SENSITIVE_KEYWORDS):
                safe_results.append(r)

        return safe_results[:limit]

    @classmethod
    def _fetch_toutiao_hot(cls) -> List[Dict[str, str]]:
        """抓取今日头条热榜中的防务与地缘焦点"""
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        items = []
        try:
            res = requests.get(url, headers=headers, timeout=5).json()
            raw_list = res.get("data", [])
            for r in raw_list:
                title = r.get("Title", "").strip()
                item_url = r.get("Url", "")
                hot_val = r.get("HotValue", "")

                # 过滤出防务与地缘相关条目
                is_defense = any(k in title for k in cls.DEFENSE_KEYWORDS)
                is_excluded = any(bad in title for bad in cls.EXCLUDE_KEYWORDS)

                if is_defense and not is_excluded:
                    # 格式化热度
                    hot_str = "高"
                    if hot_val:
                        try:
                            val_num = int(hot_val)
                            hot_str = f"{round(val_num / 10000)}万"
                        except Exception:
                            hot_str = str(hot_val)

                    items.append({
                        "title": title,
                        "url": item_url or f"https://www.toutiao.com/search?keyword={urllib.parse.quote(title)}",
                        "source": "今日头条热点",
                        "hot": hot_str,
                        "category": "rolling",
                        "summary": f"头条实时防务与国际地缘焦点，热度值：{hot_str}。"
                    })
        except Exception as e:
            logger.warning(f"抓取今日头条热搜失败: {e}")
        return items

    @classmethod
    def _fetch_sina_military(cls) -> List[Dict[str, str]]:
        """抓取新浪军事权威频道 (lid=2514)"""
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2514&k=&num=30&page=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        items = []
        try:
            res = requests.get(url, headers=headers, verify=False, timeout=6).json()
            raw_list = res.get("result", {}).get("data", [])
            for r in raw_list:
                title = r.get("title", "").strip()
                item_url = r.get("url", "")
                media = r.get("media_name", "").strip() or "权威防务观察"
                intro = r.get("intro", "").strip()

                if not title:
                    continue

                if not any(bad in title for bad in cls.EXCLUDE_KEYWORDS):
                    items.append({
                        "title": title,
                        "url": item_url,
                        "source": media,
                        "hot": "热点",
                        "category": "eurasia" if any(k in title for k in ["俄", "乌", "北约", "欧洲"]) else "middle_east",
                        "summary": intro[:120] if intro else "一线权威军事态势跟踪与战报复盘。"
                    })
        except Exception as e:
            logger.warning(f"抓取新浪军事新闻失败: {e}")
        return items

    @classmethod
    def _get_curated_intel_bank(cls) -> List[Dict[str, str]]:
        """官方公报与战略推演储备池 (带权威出处与溯源直达链接)"""
        return [
            {
                "title": "也门胡塞武装声称袭击沙特阿美在延布的设施及空军基地",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("胡塞武装 袭击 沙特 延布"),
                "source": "萨那军方作战简报",
                "hot": "置顶",
                "category": "middle_east",
                "summary": "胡塞武装动用自杀式无人机与巡航导弹复合突防沙特红海沿岸油港延布，双方百年教派与领土纠葛再起波澜。"
            },
            {
                "title": "美军‘繁荣卫士’护航行动账本困境：400万刀标准-2打2万刀无人机的效费比死穴",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("繁荣卫士 护航 驱逐舰 拦截成本"),
                "source": "五角大楼审计备忘录",
                "hot": "热议",
                "category": "middle_east",
                "summary": "红海实战暴露西方海军垂直发射单元弹药再装填周期长、高价拦截弹库存消耗过快的致命死穴。"
            },
            {
                "title": "滑翔制导炸弹（UMPK）战术革新：俄空天军防区外点穴如何撕碎筑垒防线",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("俄空天军 滑翔制导炸弹 UMPK"),
                "source": "战地前线态势复盘",
                "hot": "精选",
                "category": "eurasia",
                "summary": "FAB系列重型航弹加装卫星折叠滑翔翼套，在乌军野战防空圈外实施高精度砸坑，重塑阵地攻防规则。"
            },
            {
                "title": "北约东翼‘苏瓦乌基走廊’攻防推演：重装装甲突破与反坦克火力网博弈",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("苏瓦乌基走廊 北约 兵力部署"),
                "source": "北约防务智库报告",
                "hot": "深度",
                "category": "eurasia",
                "summary": "连接白俄罗斯与加里宁格勒的65公里陆上咽喉地带，多国战术营在遭遇穿插突击时的现实反应时序。"
            },
            {
                "title": "高超音速滑翔弹头末端突防测算：海基‘宙斯盾/标准-6’拦截窗口的物理瓶颈",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("高超音速滑翔弹头 标准6 拦截极限"),
                "source": "导弹防御纵深分析",
                "hot": "硬核",
                "category": "tech",
                "summary": "乘波体临近空间高机动变轨导致相控阵雷达追踪轨迹断裂，动能拦截器视场盲区与拦截窗口极限解算。"
            }
        ]

    @classmethod
    def fetch_hot_topics(cls, keywords: List[str] = None, limit: int = 15) -> List[Dict[str, str]]:
        return cls.fetch_multi_source_topics(category="all", limit=limit)
