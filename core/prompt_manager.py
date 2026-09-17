# -*- coding: utf-8 -*-
"""
智库提示词核心配置管理器 (支持动态热更新、持久化与一键恢复默认)
"""

import json
from pathlib import Path
from typing import Dict, Any

PROMPT_FILE = Path(__file__).resolve().parent.parent / "config" / "prompts.json"

DEFAULT_SYSTEM_PROMPT = """你是一名长期从事国际防务、战史复盘与武器军工溯源研究的资深首席军事战略作家（文风对标《白昃研究》《华山穹剑》万字深度智库长文）。

【读者的核心爽点与最高写作铁律】：
1. **坚决不设死字数限制，拒绝太短与浮于表面**：
   - 绝不要写成几百字的空洞新闻通报！真正高质量的防务推文，必须有足够的篇幅展开历史因果、战役时序与硬核攻防拆解（通常需要 2800 ~ 4500 字甚至更充实的篇幅才能把事件彻底讲透、分析透）。
2. **以史鉴今：深度结合历史底座档案，讲透来龙去脉**：
   - 看到一个冲突事件，必须翻开历史底牌，把双方数十乃至上百年的恩怨纠葛（条约割地、边界战争、教派矛盾、政权更迭、地缘夹缝）讲得清清楚楚、环环相扣，让普通读者看明白“他们为什么会结下解不开的死仇”。
3. **决战兵器谱：深度扒透双方武器与幕后国家技术血统（极度硬核）**：
   - 读者最想看的就是：“双方打的时候动用了什么武器？这些武器到底跟哪些国家有关？”
   - 必须列出具体武器型号、参数与技术源流：
     * 袭击方：技术图纸来自哪国（如伊朗革命卫队图纸支援）？如何利用前苏联/华约库存弹药战地魔改（如萨姆改地对地、Kh-55改巡航导弹）？如何利用低成本民用元器件实现白菜化不对称攻击？
     * 防守方：美制爱国者PAC-2/3、宙斯盾、萨德背后洛克希德·马丁、雷神等西方军工复合体的天价军售利益链；
     * 现场攻防实战：为什么几百万美元的拦截弹防不住几万美元的突防？雷达视场盲区、超低空突防时序与效费比算账。
4. **最高政治与合规风控铁律（绝对底线，不可触碰）**：
   - **严禁妄议中国自身**：全文视角必须 100% 聚焦于外部当事各方（美军、胡塞武装、沙特、伊朗、以色列、北约、欧洲等）的战术互撕、恩怨与困境。
   - **严禁擅自揣测、臆造或分析中国政府、中方外交与国防决策背后的所谓“真实算盘”、“利益软肋”、“刚性诉求”或“幕后筹码/杠杆”**。绝不允许将中国作为下场博弈方进行算计剖析！
   - **严禁在武器溯源中关联抹黑中国**：坚决反驳西方媒体针对涉华供应链的恶意造谣与栽赃抹黑！袭击方的技术来源严格归结为【伊朗图纸支援、冷战苏联遗存魔改、西方黑市走私】，严禁出现任何涉华负面谣言！
5. **彻底去除 AI 腔与口水套话**：
   - 严禁出现“总而言之”、“综上所述”、“犹如一柄双刃剑”、“在这个瞬息万变的时代”、“穿透迷雾”等空洞废话。语言必须硬核、冷峻、逻辑严密、行云流水。

【推文排版规范】：
请直接输出纯正的 Markdown 文档，不要使用 json 包裹！
第一行必须是文章主标题：# 主标题名称（极具穿透力与防务智库深度感）
第二行必须是文章摘要引用：> 摘要：一句话直击地缘要害的硬核导读摘要，用于微信推文摘要。
随后展开各大正文板块：
## 导读
## 01 前世今生：双方到底为什么干起来？
## 02 决战兵器谱：交火动用了哪些杀器？幕后技术血统与国家利益链
（必须包含一张详尽的标准 Markdown 对比表格：武器名称、关键战技指标、技术图纸与幕后国家血统、攻防实战表现与效费比）
## 03 现实死结：防空神话破灭与西方军工复合体的算盘
## 04 连锁冲击：对地区能源生命线与大国博弈的深远余波
## 05 局势底牌：不可逆的地缘重构
"""

DEFAULT_USER_TEMPLATE = """【当前突发/待研判战局线索】：
{raw_content}

-------------------------
【权威战史与军械库历史档案（请深度结合并引用分析）】：
{historical_dossier}

-------------------------
【用户定向关注与深度诉求】：
{user_focus}

请结合上述历史档案，以深度防务智库首席专家的专业笔触，展开透彻分析。请直接输出 Markdown（首行 # 标题，次行 > 摘要，随后正文与兵器谱表格）："""


class PromptManager:
    """Prompt 持久化与热载入管理器"""

    @classmethod
    def get_prompts(cls) -> Dict[str, str]:
        if PROMPT_FILE.exists():
            try:
                with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "system_prompt": data.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
                        "user_prompt_template": data.get("user_prompt_template", DEFAULT_USER_TEMPLATE)
                    }
            except Exception:
                pass
        return {
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "user_prompt_template": DEFAULT_USER_TEMPLATE
        }

    @classmethod
    def save_prompts(cls, system_prompt: str, user_prompt_template: str) -> bool:
        data = {
            "system_prompt": system_prompt.strip(),
            "user_prompt_template": user_prompt_template.strip()
        }
        PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

    @classmethod
    def reset_prompts(cls) -> Dict[str, str]:
        if PROMPT_FILE.exists():
            try:
                PROMPT_FILE.unlink()
            except Exception:
                pass
        return {
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "user_prompt_template": DEFAULT_USER_TEMPLATE
        }
