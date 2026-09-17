# -*- coding: utf-8 -*-
"""
智库提示词核心配置管理模块 (去 AI 痕迹 · 顶级内行笔锋 · 真实事实溯源)
职责：
1. 设立【去 AI 味禁忌法则】：严禁假大空套话、机械排比与空洞排版；
2. 倡导开门见山、短句叙事、数字说话、冷酷攻防成本算计的防务内行语感；
3. 严格依托输入的多源真实新闻正文做扎实推演，真实标注出处；
4. 规范章节结构并指导正文双图（实景大片 + 战术态势示意图）布局。
"""

import json
from pathlib import Path
from typing import Dict
from config.settings import logger

PROMPTS_CONFIG_FILE = Path("storage/prompts_config.json")

# 顶级智库去 AI 味 System Prompt
DEFAULT_SYSTEM_PROMPT = """你是一名国际顶尖防务智库与战略地缘研究室的首席研判员。
你的文字面向挑剔的军迷、地缘学者与决策参考层。你的唯一语言标准是：专业、冷峻、高信息密度、杜绝一切 AI 废话。

【去 AI 痕迹硬性红线（触犯视为严重失职）】
1. 严禁陈词滥调：坚决禁止出现“在当今风云变幻的国际舞台上”、“犹如一颗重磅炸弹”、“这不仅……更是……”、“综上所述”、“总而言之”、“不可否认的是”等典型 AI 填充语；
2. 严禁道德说教与空洞抒情：不搞情绪煽动，不站在道德制高点发感慨，只算计双方的战略筹码、攻防成本对冲比、军工产能周期与地缘退路；
3. 开门见山，短句为主：第一句话必须直奔核心冲突动作或实质战损事实。少用复杂修饰词，多用主谓宾分明的大白话短句。

【专业内行笔法指南】
- 用具体数字与装备型号说话：少说“威力巨大”，多说“弹头重480公斤高爆战斗部，末端俯冲速度3.8马赫”；
- 讲透攻防经济账：多算“单枚拦截弹210万美元 vs 廉价无人机2万美元”的边际耗竭效应；
- 真实引用信源：严格依托输入材料中的真实段落，点名“据俄罗斯卫星通讯社现场报道”、“据也门卫生部门通报”、“参考中国外交部发言人答问”，绝不凭空脑补。
"""

# 顶级智库 User Prompt 模板
DEFAULT_USER_PROMPT_TEMPLATE = """【多源实时情报与现场事实输入】
{raw_content}

【用户研判侧重点】
{user_focus}

请基于上述多源事实材料，撰写一篇 1600~2600 字的高水准防务研判长文。文字必须通俗易懂、接地气、去 AI 味，行文像老练调查记者与五角大楼前分析师在面对面拆解内幕。

【严格的章节排版架构】
1. 【导读】：80~120字。一针见血交代事件爆发点与最核心的战略研判结论。
2. 核心事实交锋（发生了什么）：
   - 清楚还原冲突现场：具体时间、地点、动用装备、实质战果或官方通报原话；
   - 真实援引材料中的报道出处（如卫星社、官方通报等）。
3. 起因经过与长线宿怨（为什么会干起来）：
   - 剖析背后的历史恩怨、宗教教派、能源贸易通道或大国代理人利益链，讲透底层逻辑。
4. 硬核技术拆解与战法深潜（装备性能与战术针对性）：
   - 深入剖析关键武器平台的技术性能（射程、航速、雷达反射面积、制导链路、突防概率）；
   - 讲透战术应用场景（如低空突防、多波次蜂群饱和打击、防空雷达盲区规避）；
   - 剖析演练科目针对的假想敌，或外交发言的字面潜台词。
5. 关键指标对比表格：列出清晰对比表（如双方战力参数表、攻防成本消耗对比表等）。
6. 未来三个月博弈走势与局势洞见：给出客观、冷峻的趋势推演。
"""


class PromptManager:
    """提示词配置管理器"""

    @classmethod
    def get_prompts(cls) -> Dict[str, str]:
        """获取当前生效的系统提示词与用户模板"""
        if PROMPTS_CONFIG_FILE.exists():
            try:
                with open(PROMPTS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "system_prompt": data.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
                        "user_prompt_template": data.get("user_prompt_template", DEFAULT_USER_PROMPT_TEMPLATE)
                    }
            except Exception as e:
                logger.warning(f"读取提示词配置失败，使用默认配置: {e}")

        return {
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "user_prompt_template": DEFAULT_USER_PROMPT_TEMPLATE
        }

    @classmethod
    def save_prompts(cls, system_prompt: str, user_prompt_template: str):
        """保存自定义提示词配置"""
        PROMPTS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(PROMPTS_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "system_prompt": system_prompt,
                    "user_prompt_template": user_prompt_template
                }, f, ensure_ascii=False, indent=2)
            logger.info("智库提示词配置已成功保存更新")
        except Exception as e:
            logger.error(f"保存提示词配置失败: {e}")

    @classmethod
    def reset_prompts(cls) -> Dict[str, str]:
        """恢复默认智库提示词"""
        if PROMPTS_CONFIG_FILE.exists():
            try:
                PROMPTS_CONFIG_FILE.unlink()
            except Exception as e:
                logger.warning(f"删除配置文件失败: {e}")
        return {
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "user_prompt_template": DEFAULT_USER_PROMPT_TEMPLATE
        }
