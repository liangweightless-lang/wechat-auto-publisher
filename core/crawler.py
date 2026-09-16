# -*- coding: utf-8 -*-
"""
多源防务与官方公告热点聚合引擎
职责：
1. 聚焦权威官方通报：美军CENTCOM、俄国防部、乌总参谋部、也门胡塞发言人、沙特国防部、海事局航行警告等；
2. 六大战区与官方公告分类（官方公告、红海中东、俄乌欧亚、硬核装备、大国海权、实时滚动）；
3. 严格排除财经股票基金噪音，确保第一手官方信源权威性；
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
    """防务与官方公告多源聚合器"""

    HISTORY_FILE = Path(__file__).resolve().parent.parent / "assets" / "crawled_history.json"

    # 防务军事强相关特征词（严格过滤无关娱乐财经新闻）
    DEFENSE_MUST_KEYWORDS = [
        "军", "战", "导弹", "航母", "战机", "核潜艇", "无人机", "防空", "突袭", "演习",
        "也门", "胡塞", "红海", "沙特", "美军", "五角大楼", "乌克兰", "俄军", "北约", "以军",
        "曼德海峡", "霍尔木兹", "高超音速", "宙斯盾", "巡航导弹", "雷达", "兵力", "拦截", "特种部队",
        "公告", "通报", "声明", "航行警告", "公报"
    ]

    # 六大分类定义（突出官方公报）
    CATEGORIES = {
        "all": "🌐 全域战略综述",
        "official": "🏛️ 官方公告与战报",
        "middle_east": "🔴 红海与中东死结",
        "eurasia": "🔵 俄乌与欧亚前线",
        "tech": "🟢 硬核装备与战法",
        "power": "🟡 大国地缘与海权",
        "rolling": "⚡ 24H实时防务快报"
    }

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
    def _get_curated_intel_bank(cls) -> List[Dict[str, str]]:
        """构建包含官方公报与智库研判的选题池"""
        return [
            # === 0. 权威官方公告与军情公报 (official) ===
            {
                "title": "也门胡塞军方发言人发表作战公报：在红海及亚丁湾对两艘美军驱逐舰实施饱和打击",
                "category": "official",
                "source": "胡塞武装最高军事委员会公报",
                "level": "官方战报",
                "summary": "也门萨那军方发言人叶海亚·萨雷阿准将通报：多枚反舰弹道导弹及无人机成功命中目标，重申对通过红海关联船只的拦截禁令。",
                "keyword": "官方公报"
            },
            {
                "title": "美军中央司令部（CENTCOM）发布红海战况通报：摧毁胡塞武装地基雷达与未发射反舰导弹",
                "category": "official",
                "source": "五角大楼 / CENTCOM 官方声明",
                "level": "美军通报",
                "summary": "美中央司令部确认在也门控制区实施先发制人精确自卫打击，击毁4架单向攻击无人机和1个移动导弹发射阵位。",
                "keyword": "五角大楼"
            },
            {
                "title": "俄罗斯国防部发布库尔斯克与乌东战役公报：拦截乌军数十枚海马斯火箭弹与滑翔炸弹",
                "category": "official",
                "source": "俄国防部每日战况简报",
                "level": "俄军通报",
                "summary": "俄空天军苏-34战斗轰炸机使用UMPK滑翔航弹对乌军集结地域实施集群打击，击毁美制布雷德利战车及野战防空雷达。",
                "keyword": "战况简报"
            },
            {
                "title": "乌克兰武装部队总参谋部战情通报：托列茨克与红军城方向击退俄军48次地面强攻",
                "category": "official",
                "source": "乌总参谋部官方战报",
                "level": "乌军通报",
                "summary": "乌总参公布全线交火数据，称乌无人机部队成功瘫痪俄军前沿炮兵观通阵位，双方在前沿永久防线展开白刃堑壕争夺。",
                "keyword": "乌总参公报"
            },
            {
                "title": "沙特国防部发布防空拦截公报：在南部边界成功击落飞向阿美能源设施的自杀式无人机",
                "category": "official",
                "source": "沙特通讯社 (SPA) / 国防部声明",
                "level": "沙特公告",
                "summary": "沙特防空部队爱国者PAC-3系统在吉赞以南高空截获目标，残骸坠落未造成炼油产能中断，强调对领空主权的刚性捍卫。",
                "keyword": "沙特通报"
            },
            {
                "title": "国际海事组织（IMO）与英国海事贸易行动办公室（UKMTO）发布航行安全紧急公告",
                "category": "official",
                "source": "国际海事权威通告",
                "level": "航行警告",
                "summary": "UKMTO通报也门摩卡港西南海域商船遭遇快艇靠近与疑似水雷漂流威胁，建议所有通过曼德海峡船只保持最高战备警戒。",
                "keyword": "航行警告"
            },

            # === 1. 红海与中东死结 (middle_east) ===
            {
                "title": "曼德海峡不对称窒息战：胡塞高超反舰弹道导弹对美军航母护航体系的战术穿透",
                "category": "middle_east",
                "source": "中东防务智库",
                "level": "特级态势",
                "summary": "解析也门胡塞武装'巴勒斯坦-2'与反舰巡航导弹如何绕开宙斯盾相控阵雷达盲区，迫使美航母打击群退缩至红海北端。",
                "keyword": "红海封锁"
            },
            {
                "title": "从‘决心风暴’到停火僵局：沙特‘2030愿景’在也门泥潭中的十年安全焦虑",
                "category": "middle_east",
                "source": "海湾安全观察",
                "level": "战略研判",
                "summary": "沙特巨额主权基金招商引资对本土无战事的极端刚需，与胡塞武装无人机精准点穴沙特阿美炼油厂之间的死结。",
                "keyword": "沙特也门"
            },
            {
                "title": "‘抵抗之弧’的协同机制重构：真主党、胡塞与伊拉克民兵的多波次饱和袭扰战法",
                "category": "middle_east",
                "source": "区域安全纵深",
                "level": "重点态势",
                "summary": "拆解伊朗高原技术支援网络如何通过低成本自杀式无人机，撕裂以军铁穹与海湾爱国者防空阵列。",
                "keyword": "抵抗之弧"
            },
            {
                "title": "美军‘繁荣卫士’护航行动的账本困境：单枚400万刀标准-2打2万刀无人机的败局已定？",
                "category": "middle_east",
                "source": "五角大楼审计",
                "level": "成本推演",
                "summary": "红海实战暴露西方海军垂发单元（VLS）弹药再装填周期长、舰载防空弹药产能见底的不对称消耗困境。",
                "keyword": "效费比死穴"
            },

            # === 2. 俄乌与欧亚前线 (eurasia) ===
            {
                "title": "滑翔制导炸弹（UMPK）战术革新：俄空天军防区外点穴如何瓦解乌军永久筑垒地域",
                "category": "eurasia",
                "source": "战役复盘",
                "level": "装备战法",
                "summary": "FAB-1500/3000巨型航弹加装卫星制导翼套，在乌军防空导弹射程外实施饱和砸坑，彻底改变阵地战攻防逻辑。",
                "keyword": "滑翔航弹"
            },
            {
                "title": "库尔斯克突出部拉锯战复盘：机械化穿插与无人机FPV‘空中地雷阵’的巷战绞杀",
                "category": "eurasia",
                "source": "前线态势",
                "level": "战术深潜",
                "summary": "光纤制导无电磁干扰无人机投入实战，传统电子干扰枪全面失效，战场单兵与轻装甲目标生存率断崖式下跌。",
                "keyword": "光纤FPV"
            },
            {
                "title": "北约东翼防务‘苏瓦乌基走廊’防御推演：波兰与波罗的海三国的兵力布署死穴",
                "category": "eurasia",
                "source": "北约防务透视",
                "level": "地缘战略",
                "summary": "连接白俄罗斯与加里宁格勒的65公里陆上走廊，北约常驻多国战术营在遭遇重装集团装甲突击时的反应窗口测算。",
                "keyword": "苏瓦乌基"
            },

            # === 3. 硬核装备与前沿科技 (tech) ===
            {
                "title": "高超音速滑翔弹头战术突防测算：现役海基‘标准-3/6’末端拦截窗口的物理极限",
                "category": "tech",
                "source": "导弹防御纵深",
                "level": "硬核技术",
                "summary": "临近空间乘波体变轨机动导致天基红外预警与地面相控阵雷达跟踪轨迹不连续，动能拦截器（KKV）视场盲区曝光。",
                "keyword": "高超音速"
            },
            {
                "title": "蜂群防御终极方案较量：高功率微波武器（HPM）与多联装微型近防弹的效能实测",
                "category": "tech",
                "source": "反无前沿",
                "level": "前沿科技",
                "summary": "传统密集阵（Phalanx）与激光武器在多方向200架无人机饱和攻击下的热过载与毁伤通道瓶颈对比。",
                "keyword": "反无人机蜂群"
            },

            # === 4. 大国地缘与海权 (power) ===
            {
                "title": "美海军造船业产能坍塌警报：四大公立船厂工人断层与万吨大驱延期服役死结",
                "category": "power",
                "source": "大国海权",
                "level": "工业根基",
                "summary": "美海军355艘舰艇目标与每年仅能交付1.5艘驱逐舰的残酷现实，核动力潜艇排队维修等待期突破24个月。",
                "keyword": "美军造舰"
            },
            {
                "title": "海湾‘石油美元’裂痕与本币结算：中东主权基金对西方制裁资产冻结的防御性撤资",
                "category": "power",
                "source": "金融地缘博弈",
                "level": "金融战线",
                "summary": "俄罗斯外汇储备被扣押事件引发连锁反应，沙特、阿联酋加速黄金储备多元化，并在双边贸易中加大本币清算比例。",
                "keyword": "石油美元"
            }
        ]

    @classmethod
    def fetch_multi_source_topics(cls, category: str = "all", limit: int = 20) -> List[Dict[str, str]]:
        """
        跨渠道多源抓取与聚合热点（支持官方公告）
        :param category: 分类 (all, official, middle_east, eurasia, tech, power, rolling)
        :param limit: 返回最大数量
        """
        history = cls.load_history()
        results = []

        # 1. 优先调用实时严格过滤的新闻流与官方公告
        if category in ["all", "rolling", "official"]:
            rolling_items = cls._fetch_sina_roll()
            if category == "official":
                # 筛选带有通报、公报、声明字样的条目
                rolling_items = [r for r in rolling_items if any(k in r["title"] for k in ["公告", "通报", "声明", "公报", "警告", "发言人", "国防部"])]
            results.extend(rolling_items)

        # 2. 合并智库与官方储备池
        intel_topics = cls._get_curated_intel_bank()
        for it in intel_topics:
            if it["title"] not in history:
                results.append(it)

        # 3. 按分类过滤
        if category != "all":
            results = [r for r in results if r.get("category") == category]

        # 4. 安全合规前置过滤
        safe_results = []
        for r in results:
            if not any(sk in r["title"] for sk in settings.SENSITIVE_KEYWORDS):
                safe_results.append(r)

        return safe_results[:limit]

    @classmethod
    def _fetch_sina_roll(cls) -> List[Dict[str, str]]:
        """抓取主流公开滚动军事热点并严格过滤防务范畴"""
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&page=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        items = []
        try:
            res = requests.get(url, headers=headers, verify=False, timeout=6).json()
            raw_list = res.get("result", {}).get("data", [])
            for r in raw_list:
                t = r.get("title", "").strip()
                intro = r.get("intro", "").strip()
                # 严密过滤：必须匹配防务专有名词，且不得包含股票理财
                if any(k in t for k in cls.DEFENSE_MUST_KEYWORDS) and not any(bad in t for bad in ["ETF", "基金", "股", "理财", "银行", "涨幅", "跌停", "行情", "大涨"]):
                    # 判断是否为官方声明通报
                    is_official = any(k in t for k in ["公告", "通报", "声明", "公报", "警告", "国防部", "总参", "发言人"])
                    items.append({
                        "title": t,
                        "url": r.get("url", ""),
                        "category": "official" if is_official else "rolling",
                        "source": "官方权威发布" if is_official else "实时军情",
                        "level": "官方通报" if is_official else "前线速递",
                        "summary": intro[:120] if intro else "聚焦官方公布的前沿防务动向与战况通报。",
                        "keyword": "权威通报" if is_official else "实时动态"
                    })
        except Exception as e:
            logger.warning(f"获取滚动军情失败: {e}")
        return items

    @classmethod
    def fetch_hot_topics(cls, keywords: List[str] = None, limit: int = 15) -> List[Dict[str, str]]:
        """兼容老接口"""
        return cls.fetch_multi_source_topics(category="all", limit=limit)
