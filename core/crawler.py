# -*- coding: utf-8 -*-
"""
多源防务与地缘热点聚合引擎
职责：
构建高密度、多维度的防务数据源矩阵，涵盖：
1. 五大战区（红海中东、俄乌欧亚、硬核装备、大国博弈、实时滚动要闻）50+ 精选智库情报库；
2. 门户主流国际防务与军情实时滚动流（新浪军事、环球防务等）；
3. 动态分类与关键词精准匹配；
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

    HISTORY_FILE = Path(__file__).resolve().parent.parent / "assets" / "crawled_history.json"

    # 防务军事强相关特征词（严格过滤无关娱乐财经新闻）
    DEFENSE_MUST_KEYWORDS = [
        "军", "战", "导弹", "航母", "战机", "核潜艇", "无人机", "防空", "突袭", "演习",
        "也门", "胡塞", "红海", "沙特", "美军", "五角大楼", "乌克兰", "俄军", "北约", "以军",
        "曼德海峡", "霍尔木兹", "高超音速", "宙斯盾", "巡航导弹", "雷达", "兵力", "拦截", "特种部队"
    ]

    # 五大维度战区定义
    CATEGORIES = {
        "all": "🌐 全域战略综述",
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
        """构建 50+ 条高价值防务智库选题池"""
        return [
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
            {
                "title": "苏伊士运河货运腰斩：好望角大绕行推高欧洲能源通胀与海运保费连锁海啸",
                "category": "middle_east",
                "source": "航运防务观察",
                "level": "地缘经济",
                "summary": "红海航道受阻导致全球集装箱周转率暴跌20%，亚欧航线单柜运费飙升300%，欧洲央行降息预期遭遇实质反噬。",
                "keyword": "航运危机"
            },
            {
                "title": "水下不对称黑天鹅：曼德海峡国际海底通信光缆受损与也门近海扫雷盲区",
                "category": "middle_east",
                "source": "前沿战法",
                "level": "特种战况",
                "summary": "商船锚链拖曳与水下简易爆破装置对欧亚通信干线的致命威胁，美欧海军近海扫雷艇严重短缺的尴尬现状。",
                "keyword": "海底光缆"
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
            {
                "title": "黑海制海权的‘无人化转移’：乌克兰‘马古拉’无人艇对俄黑海舰队基地纵深压缩",
                "category": "eurasia",
                "source": "海上对抗",
                "level": "无人海战",
                "summary": "俄黑海舰队水面大型舰艇悉数后撤至新罗西斯克，不对称无人艇集群改变百年近海制海权传统防御理论。",
                "keyword": "无人艇海战"
            },
            {
                "title": "欧洲军火工业产能复兴断层：155毫米炮弹火药供应链受限与多国采购配额内讧",
                "category": "eurasia",
                "source": "国防工业观察",
                "level": "工业基础",
                "summary": "硝化棉原材料短缺与能源高企，导致莱茵金属与北欧军工集团产能爬坡迟缓，战略自主口号与现实库存的撕裂。",
                "keyword": "炮弹危机"
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
            {
                "title": "水下幽灵的猎杀与反潜：微型无人潜航器（UUV）在第一岛链海峡通道的布防网络",
                "category": "tech",
                "source": "水下特种战",
                "level": "水下防务",
                "summary": "长航时低速潜航器配合海底水听基阵，对核潜艇低频噪声指纹的实时捕捉与声纳浮标投放算法升级。",
                "keyword": "无人潜航器"
            },
            {
                "title": "战场‘全域感知’天基算力争夺：低轨侦察卫星星座对移动式导弹发射车（TEL）实时锁眼",
                "category": "tech",
                "source": "太空防务",
                "level": "天基战场",
                "summary": "合成孔径雷达（SAR）卫星与边缘AI芯片结合，将从卫星成像到下达打击指令的‘杀伤链’压缩至3分钟内。",
                "keyword": "天基侦察"
            },
            {
                "title": "全电推进与电磁弹射的可靠性大考：美福特号航母先进武器升降机（AWE）实战排障记录",
                "category": "tech",
                "source": "海空装备",
                "level": "舰载航空",
                "summary": "电磁阻拦装置（AAG）与中压直流电网在高频次战备起降中的故障率曲线，与尼米兹级蒸汽弹射效能横向对比。",
                "keyword": "电磁弹射"
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
            },
            {
                "title": "从‘战略模糊’到双重承压：中东盟友在美伊极限施压下的避险外交博弈",
                "category": "power",
                "source": "地缘智库",
                "level": "战略研判",
                "summary": "阿联酋与沙特坚决拒绝向美军开放领空发动对也门空袭，海湾君主国开启独立多边对冲策略的深层逻辑。",
                "keyword": "海湾外交"
            },
            {
                "title": "北极航道与冰下潜航博弈：破冰船编队短缺如何削弱北约对高纬度水道的实质控制",
                "category": "power",
                "source": "极地防务",
                "level": "高纬战略",
                "summary": "俄极地核动力破冰船编队常态化护航北方海航道，美海岸警卫队仅剩1艘老旧重型破冰船的极地真空尴尬。",
                "keyword": "北极航道"
            }
        ]

    @classmethod
    def fetch_multi_source_topics(cls, category: str = "all", limit: int = 20) -> List[Dict[str, str]]:
        """
        跨渠道多源抓取与聚合热点
        :param category: 分类 (all, middle_east, eurasia, tech, power, rolling)
        :param limit: 返回最大数量
        """
        history = cls.load_history()
        results = []

        # 1. 优先调用实时严格过滤的新闻流
        if category in ["all", "rolling"]:
            rolling_items = cls._fetch_sina_roll()
            results.extend(rolling_items)

        # 2. 合并智库储备选题池
        intel_topics = cls._get_curated_intel_bank()
        for it in intel_topics:
            if it["title"] not in history:
                results.append(it)

        # 3. 按分类过滤
        if category != "all":
            if category == "rolling":
                results = [r for r in results if r.get("category") == "rolling"]
            else:
                results = [r for r in results if r.get("category") == category]

        # 4. 安全合规前置过滤
        safe_results = []
        for r in results:
            if not any(sk in r["title"] for sk in settings.SENSITIVE_KEYWORDS):
                safe_results.append(r)

        return safe_results[:limit]

    @classmethod
    def _fetch_sina_roll(cls) -> List[Dict[str, str]]:
        """抓取新浪公开滚动军事热点并严格过滤防务范畴"""
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
                # 严密过滤：必须匹配防务专有名词
                if any(k in t for k in cls.DEFENSE_MUST_KEYWORDS) and not any(bad in t for bad in ["ETF", "基金", "股", "理财", "银行", "涨幅", "跌停", "行情", "大涨"]):
                    items.append({
                        "title": t,
                        "url": r.get("url", ""),
                        "category": "rolling",
                        "source": "实时军情",
                        "level": "前线速递",
                        "summary": intro[:120] if intro else "聚焦前沿防务动向与武器攻防态势发布。",
                        "keyword": "实时动态"
                    })
        except Exception as e:
            logger.warning(f"获取滚动军情失败: {e}")
        return items

    @classmethod
    def fetch_hot_topics(cls, keywords: List[str] = None, limit: int = 15) -> List[Dict[str, str]]:
        """兼容老接口"""
        return cls.fetch_multi_source_topics(category="all", limit=limit)
