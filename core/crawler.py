# -*- coding: utf-8 -*-
"""
多源防务与地缘热点聚合引擎
职责：
构建多维数据源矩阵，涵盖：
1. 门户主流国际防务新闻流（新浪军事等）；
2. 中东/红海/大国博弈四大主题智库选题池；
3. 网页长文与外媒智库译萃快速提取；
4. 历史去重与前置安全合规风控。
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
    """防务与国际热点多源聚合器"""

    # 重点关注的关键词群组
    KEYWORDS_MIDDLE_EAST = ["红海", "曼德海峡", "胡塞武装", "也门", "沙特", "伊朗", "以色列"]
    KEYWORDS_TECH_WEAPON = ["无人机", "防空系统", "巡航导弹", "高超音速", "航母", "驱逐舰", "雷达"]
    KEYWORDS_BIG_POWER = ["美军", "北约", "印太", "地缘博弈", "兵力部署", "军事演习"]

    HISTORY_FILE = Path(__file__).resolve().parent.parent / "assets" / "crawled_history.json"

    @classmethod
    def load_history(cls) -> set:
        """加载已抓取发布过的文章标题指纹"""
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
    def fetch_multi_source_topics(cls, category: str = "all", limit: int = 8) -> List[Dict[str, str]]:
        """
        跨渠道多源抓取与聚合热点
        :param category: 分类 (all, middle_east, tech, power)
        :param limit: 返回最大数量
        """
        history = cls.load_history()
        results = []

        # 渠道 1：公开国际防务滚动流
        sina_topics = cls._fetch_sina_roll()
        for t in sina_topics:
            if t["title"] not in history:
                results.append(t)

        # 渠道 2：精选防务智库战术态势情报池 (对标顶级防务公号核心关注点)
        intel_topics = [
            # 中东与红海关键航道
            {
                "title": "曼德海峡制海权争夺：胡塞武装巡飞弹与反舰弹道导弹饱和突防战术复盘",
                "category": "middle_east",
                "source": "智库态势速递",
                "summary": "深入剖析也门沿岸固定式地下发射阵地与移动式低成本发射架的防侦察协同。",
                "keyword": "红海/胡塞"
            },
            {
                "title": "沙特与阿联酋也门南部利益裂痕：红海沿岸港口控制权台前幕后",
                "category": "middle_east",
                "source": "地缘观察",
                "summary": "复盘亚丁湾与荷台达港周边派系割据，沙特空军维持空中打击的后勤与外交真实代价。",
                "keyword": "沙特/中东"
            },
            {
                "title": "红海护航编队弹药库存隐忧：美英驱逐舰‘标准-2’与‘海毒蛇’高消耗困局",
                "category": "middle_east",
                "source": "防务装备",
                "summary": "单发数百万元防空导弹拦截数万元土制无人机，西方海军持续部署能力的经济临界点。",
                "keyword": "美军航母"
            },
            # 硬核防务与前沿科技
            {
                "title": "现代防空系统的致命盲区：低慢小无人机蜂群如何穿透相控阵雷达低空盲区",
                "category": "tech",
                "source": "硬科技拆解",
                "summary": "拆解多波段雷达杂波抑制算法漏洞，以及定向能/激光反无人机武器列装的技术瓶颈。",
                "keyword": "无人机防务"
            },
            {
                "title": "水下不对称博弈：微型无人潜航器与海底光缆/管线安全新威胁",
                "category": "tech",
                "source": "前沿战法",
                "summary": "从红海数条国际海底通信光缆受损事件出发，分析大国水下基础设施攻防演变。",
                "keyword": "水下特种战"
            },
            {
                "title": "高超音速滑翔弹头战术推演：现役海基标准-3/6反导系统的末端拦截概率",
                "category": "tech",
                "source": "武器前沿",
                "summary": "针对临近空间机动变轨弹头的红外探测与动能拦截器（KKV）姿控响应极限测算。",
                "keyword": "高超音速"
            },
            # 大国地缘与海空博弈
            {
                "title": "美海军造船产能危机：攻击型核潜艇维修积压与水面舰艇延寿困境",
                "category": "power",
                "source": "大国博弈",
                "summary": "美四大公立造船厂劳动力断层、零部件供应链断裂对第七、第五舰队全球巡航周期的实质压制。",
                "keyword": "美军造舰"
            },
            {
                "title": "北约东翼防线演训动态：波罗的海海空封锁战术演练背后的兵力算盘",
                "category": "power",
                "source": "欧洲防务",
                "summary": "立陶宛与波兰苏瓦乌基走廊防御节点部署，以及电子战干扰装置在实际战备中的测试表现。",
                "keyword": "北约防务"
            }
        ]

        for it in intel_topics:
            if it["title"] not in history:
                results.append(it)

        # 分类过滤
        if category != "all":
            results = [r for r in results if r.get("category") == category]

        # 安全审查过滤
        safe_results = []
        for r in results:
            if not any(sk in r["title"] for sk in settings.SENSITIVE_KEYWORDS):
                safe_results.append(r)

        return safe_results[:limit]

    @classmethod
    def _fetch_sina_roll(cls) -> List[Dict[str, str]]:
        """抓取新浪公开滚动军事热点"""
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=30&page=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        items = []
        try:
            res = requests.get(url, headers=headers, verify=False, timeout=8).json()
            raw_list = res.get("result", {}).get("data", [])
            for r in raw_list:
                t = r.get("title", "").strip()
                intro = r.get("intro", "").strip()
                # 必须符合防务/军工/战略范畴
                if any(k in t for k in ["军", "战", "美", "俄", "航母", "舰", "机", "弹", "海峡", "红海"]):
                    items.append({
                        "title": t,
                        "url": r.get("url", ""),
                        "category": "power",
                        "source": "实时滚动要闻",
                        "summary": intro[:100],
                        "keyword": "要闻聚焦"
                    })
        except Exception as e:
            logger.warning(f"获取滚动要闻失败: {e}")
        return items

    @classmethod
    def fetch_hot_topics(cls, keywords: List[str] = None, limit: int = 5) -> List[Dict[str, str]]:
        """兼容老接口"""
        return cls.fetch_multi_source_topics(category="all", limit=limit)
