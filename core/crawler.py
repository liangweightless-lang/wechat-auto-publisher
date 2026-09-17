# -*- coding: utf-8 -*-
"""
产品级多源防务与地缘热点聚合引擎
支持四大垂直选题体系：
1. 国际军事热点 (military_hot) - 军事科技/新武器、战术战法(马赛克战/无人作战)、地区冲突、国际演习、军事论坛
2. 深度国际关系 (relations) - 事件多期长线裂变、百年历史宿怨、宗教/民族/经济矛盾深度剖析
3. 先进武器追踪 (weapons) - 美/俄/日/欧主战装备与前沿武器平台性能参数与实战运用
4. 国家地区舆情 (regional_intel) - 南海、台海等区域一个月动态聚合与周边国家动向企图挖掘
"""

import json
import time
import datetime
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
import urllib3
urllib3.disable_warnings()

from config.settings import settings, logger


class DefenseCrawler:
    """防务智库多源聚合器 (四大垂直选题体系驱动)"""

    HISTORY_FILE = Path(__file__).resolve().parent.parent / "assets" / "crawled_history.json"

    CATEGORIES = {
        "all": "🌐 全部焦点",
        "military_hot": "💥 国际军事热点",
        "relations": "🤝 深度国际关系",
        "weapons": "🚀 先进武器追踪",
        "regional_intel": "🗺️ 区域舆情动向"
    }

    DEFENSE_KEYWORDS = [
        "军事", "军演", "军方", "国防部", "导弹", "航母", "战机", "核潜艇", "无人机",
        "防空", "突袭", "演习", "也门", "胡塞", "红海", "沙特", "美军", "五角大楼",
        "乌克兰", "俄军", "北约", "以色列", "以军", "哈马斯", "真主党", "伊朗",
        "曼德海峡", "霍尔木兹", "高超音速", "宙斯盾", "巡航导弹", "防区外", "拦截",
        "作战公报", "前线态势", "战报", "空袭", "交火", "停火", "兵力部署", "核武器",
        "外长", "太空武器", "遏制", "打击", "制裁", "香山论坛", "马赛克战", "南海"
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
    def _is_stale(cls, url: str, dt_str: str = "") -> bool:
        stale_patterns = ["/2021", "/2022", "/2023", "/2024", "/2025-", "2023-", "2024-"]
        if any(p in url for p in stale_patterns):
            return True
        if dt_str and any(y in dt_str for y in ["2021", "2022", "2023", "2024"]):
            return True
        return False

    @classmethod
    def _format_time(cls, ts: Optional[int] = None, dt_str: Optional[str] = None) -> str:
        now = datetime.datetime.now()
        if ts:
            target_dt = datetime.datetime.fromtimestamp(ts)
        elif dt_str:
            try:
                from email.utils import parsedate_to_datetime
                target_dt = parsedate_to_datetime(dt_str)
            except Exception:
                return "2026最新"
        else:
            return "2026最新"

        diff = now - target_dt.replace(tzinfo=None)
        seconds = diff.total_seconds()
        if seconds < 0 or seconds < 300:
            return "刚刚"
        elif seconds < 3600:
            return f"{max(1, int(seconds // 60))}分钟前"
        elif seconds < 86400:
            return f"{int(seconds // 3600)}小时前"
        else:
            return target_dt.strftime("%m-%d %H:%M")

    @classmethod
    def _classify_topic(cls, title: str, summary: str = "") -> str:
        """基于产品四大方向的智能分类器"""
        text = title + " " + summary
        if any(k in text for k in ["南海", "台海", "仁爱礁", "黄岩岛", "菲律宾", "周边国家动向", "舆情"]):
            return "regional_intel"
        if any(k in text for k in ["武器", "战机", "航母", "导弹", "F-35", "苏-57", "高超音速", "核潜艇", "性能参数", "近防", "微波武器", "防空系统"]):
            return "weapons"
        if any(k in text for k in ["条约", "宿怨", "起因经过", "教派", "宗教", "什叶派", "逊尼派", "制裁", "大国博弈", "外交", "演进", "裂变"]):
            return "relations"
        return "military_hot"

    @classmethod
    def fetch_multi_source_topics(cls, category: str = "all", limit: int = 20) -> List[Dict[str, Any]]:
        """
        跨渠道多源抓取热点并按四大垂直体系归类
        """
        history = cls.load_history()
        raw_items = []

        # 1. 抓取外网官方权威源 (俄罗斯卫星通讯社 2026 实时流)
        sputnik_topics = cls._fetch_sputnik_official()
        raw_items.extend(sputnik_topics)

        # 2. 抓取今日头条 2026 实时防务焦点
        tt_topics = cls._fetch_toutiao_hot()
        raw_items.extend(tt_topics)

        # 3. 补充四大垂直体系精选智库战报池
        curated = cls._get_curated_product_intel_bank()
        raw_items.extend(curated)

        # 去重与分类过滤
        seen_titles = set(history)
        filtered_results = []

        for item in raw_items:
            t = item["title"]
            if t in seen_titles:
                continue
            seen_titles.add(t)

            # 自动补全分类
            if "category" not in item or not item["category"]:
                item["category"] = cls._classify_topic(t, item.get("summary", ""))

            # 按用户请求的分类过滤
            if category != "all" and item["category"] != category:
                continue

            # 安全合规前置过滤
            if any(sk in t for sk in settings.SENSITIVE_KEYWORDS):
                continue

            filtered_results.append(item)

        return filtered_results[:limit]

    @classmethod
    def _fetch_sputnik_official(cls) -> List[Dict[str, Any]]:
        url = "https://sputniknews.cn/export/rss2/archive/index.xml"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        items = []
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for it in root.findall('.//item')[:30]:
                    title_el = it.find('title')
                    link_el = it.find('link')
                    pub_el = it.find('pubDate')
                    if title_el is None or not title_el.text:
                        continue

                    title = title_el.text.strip()
                    link = link_el.text.strip() if link_el is not None else ""
                    pub_str = pub_el.text.strip() if pub_el is not None else ""

                    if cls._is_stale(link, pub_str):
                        continue

                    is_defense = any(k in title for k in cls.DEFENSE_KEYWORDS)
                    is_excluded = any(bad in title for bad in cls.EXCLUDE_KEYWORDS)

                    if is_defense and not is_excluded:
                        time_tag = cls._format_time(dt_str=pub_str)
                        cat = cls._classify_topic(title)
                        items.append({
                            "title": title,
                            "url": link,
                            "source": "卫星社·外网官方",
                            "is_overseas": True,
                            "pub_time": time_tag,
                            "hot": "国际一手",
                            "category": cat,
                            "summary": f"2026年9月国际外网官方权威战报，发布于 {time_tag}。"
                        })
        except Exception as e:
            logger.warning(f"抓取外网官方源失败: {e}")
        return items

    @classmethod
    def _fetch_toutiao_hot(cls) -> List[Dict[str, Any]]:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {"User-Agent": "Mozilla/5.0"}
        items = []
        try:
            res = requests.get(url, headers=headers, timeout=5).json()
            for r in res.get("data", []):
                title = r.get("Title", "").strip()
                item_url = r.get("Url", "")
                hot_val = r.get("HotValue", "")

                is_defense = any(k in title for k in cls.DEFENSE_KEYWORDS)
                is_excluded = any(bad in title for bad in cls.EXCLUDE_KEYWORDS)

                if is_defense and not is_excluded:
                    hot_str = "高"
                    if hot_val:
                        try:
                            val_num = int(hot_val)
                            hot_str = f"{round(val_num / 10000)}万"
                        except Exception:
                            hot_str = str(hot_val)

                    cat = cls._classify_topic(title)
                    items.append({
                        "title": title,
                        "url": item_url or f"https://www.toutiao.com/search?keyword={urllib.parse.quote(title)}",
                        "source": "今日头条热点",
                        "is_overseas": False,
                        "pub_time": "今日最新",
                        "hot": hot_str,
                        "category": cat,
                        "summary": f"2026年9月头条实时防务热榜，热度：{hot_str}。"
                    })
        except Exception as e:
            logger.warning(f"抓取今日头条热搜失败: {e}")
        return items

    @classmethod
    def _get_curated_product_intel_bank(cls) -> List[Dict[str, Any]]:
        """四大垂直选题体系专属标杆智库库"""
        return [
            # === 1. 国际军事热点 (军事科技/战法/冲突/演习/论坛) ===
            {
                "title": "‘马赛克战’在红海实战中的初级形态：胡塞多维异构无人蜂群与分布式杀伤拆解",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("马赛克战 无人蜂群 红海实战"),
                "source": "军事学术与战法透视",
                "is_overseas": False,
                "pub_time": "战术专栏",
                "hot": "爆款研判",
                "category": "military_hot",
                "summary": "从战术学术角度，剖析由廉价民用组装体、老式反舰弹和无人巡飞弹构成的弹性作战网络如何让美军传统集中指挥链路失效。"
            },
            {
                "title": "美日澳‘漆黑-2026’跨国多空协同联合演习：针对南海与西太练了什么核心课目？",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("漆黑演习 美日澳 西太演练"),
                "source": "联合演习战报分析",
                "is_overseas": True,
                "pub_time": "演训深潜",
                "hot": "前沿态势",
                "category": "military_hot",
                "summary": "三国防区外隐身协同突防、敏捷战斗部署（ACE）与海空联合电子压制课目大曝光，背后战略意图深度起底。"
            },

            # === 2. 深度国际关系 (长线裂变、百年宿怨、教派与经济死结) ===
            {
                "title": "【胡塞-沙特长线专题①】从萨达贫瘠山区到红海咽喉霸主：也门胡塞武装崛起全史",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("胡塞武装发展史 萨达起义"),
                "source": "深度国际关系专辑",
                "is_overseas": False,
                "pub_time": "系列专题01",
                "hot": "专题连载",
                "category": "relations",
                "summary": "拆解1990年代青年信仰者运动起源，梳理萨利赫政权剿杀、六次萨达战争及2014年夺取首都萨那的历史裂变脉络。"
            },
            {
                "title": "【胡塞-沙特长线专题②】逊尼派王权与什叶派分支千年教派宿怨：不仅是边界争端，更是生存博弈",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("沙特 也门 宗教矛盾 瓦哈比 宰德派"),
                "source": "中东历史与宗教学术",
                "is_overseas": False,
                "pub_time": "系列专题02",
                "hot": "历史深潜",
                "category": "relations",
                "summary": "深挖瓦哈比教派扩张对也门北部传统宰德派边缘化的百年宗教排斥，剖析教派矛盾背后的民族血缘与资源争夺本质。"
            },

            # === 3. 先进武器追踪 (性能参数、战术运用与图纸源流) ===
            {
                "title": "美国‘暗鹰’LRHW高超音速导弹参数解密：乘波体滑翔弹头在亚太部署的攻防效能实测",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("美国暗鹰高超音速导弹 参数 射程"),
                "source": "开源军工装备档案",
                "is_overseas": True,
                "pub_time": "兵器谱解密",
                "hot": "硬核装备",
                "category": "weapons",
                "summary": "射程2775km、末端极速17马赫、桑格尔弹道，深入解算其第一岛链部署后对防御方相控阵预警窗口的压缩极限。"
            },
            {
                "title": "俄军苏-57配装‘产品30’发动机与小型高超音速弹：五代隐身战机防区外点穴战术运用",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("苏57 产品30发动机 战术运用"),
                "source": "战机航空动力档案",
                "is_overseas": True,
                "pub_time": "前沿航空",
                "hot": "战法推演",
                "category": "weapons",
                "summary": "推重比突破10、全向矢量喷管与机腹隐蔽弹舱适配新型Kh-69隐身巡航导弹的战区突防作战效能深度复盘。"
            },

            # === 4. 国家地区舆情追踪 (南海/台海近一月动向与企图剖析) ===
            {
                "title": "【南海近30天舆情动向大起底】周边国家频繁小动作背后的企图是什么？",
                "url": "https://www.toutiao.com/search?keyword=" + urllib.parse.quote("南海 菲律宾 美菲联演 舆情动向"),
                "source": "海洋战略与舆情监视",
                "is_overseas": False,
                "pub_time": "近月舆情大盘",
                "hot": "舆情纵深",
                "category": "regional_intel",
                "summary": "复盘过去一个月菲方在仙宾礁、仁爱礁的补给袭扰与美军外部军舰策应频率，从动向反切其配合域外大国的战术战略图谋。"
            }
        ]

    @classmethod
    def fetch_hot_topics(cls, keywords: List[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        return cls.fetch_multi_source_topics(category="all", limit=limit)
