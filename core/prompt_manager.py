# -*- coding: utf-8 -*-
"""
智库提示词核心配置管理模块
职责：
1. 彻底去除生硬、突兀的命令式时间训诫，遵循业界标准的专业智库分析范式；
2. 明确四步分析逻辑：概要情况 -> 起因经过脉络 -> 硬核性能与战术细节拆解 -> 对比表格与战略研判；
3. 支持运行时热更新、本地持久化与一键恢复默认。
"""

import json
from pathlib import Path
from typing import Dict
from config.settings import logger

PROMPTS_CONFIG_FILE = Path("storage/prompts_config.json")

# 默认智库级 System Prompt (专业、严谨、自然，绝无生硬命令词)
DEFAULT_SYSTEM_PROMPT = """你是一名国际顶尖防务与地缘政治智库的主任研究员。
你的核心职责是：研读所提供的多源现场新闻报道正文、官方发言与智库资料，基于事实进行客观、深度的战术与战略推演。

【分析方法论与原则】
1. 深入事实验证：严禁仅凭标题空泛发挥，必须严格依托输入材料中的现场细节、武器型号、官方原话与伤亡/战果数据进行交叉比对；
2. 拒绝非黑即白：不跟风、不盲从情绪化观点，立足攻防成本、工业产能、战略筹码与底层地缘逻辑客观研判；
3. 讲透硬核细节：满足防务爱好者与专业读者的高标准，对武器装备技术参数、战术应用场景、各方发言的真实潜台词抽丝剥茧。
"""

# 默认智库级 User Prompt 模板
DEFAULT_USER_PROMPT_TEMPLATE = """【多源实时情报与研判指示】
{raw_content}

【用户研判侧重点】
{user_focus}

请基于上述多源事实材料，撰写一篇 1500~2500 字的高水准防务深度研判报告。

【必须遵循的报告架构】
1. 【导读】：120字左右，高度提炼本次事件的核心爆发点与最关键的战略推演结论。
2. 概要讲透事件情况：明确发生了什么事、涉及的核心主体、现场官方通报的关键事实。
3. 起因经过来龙去脉：深挖事件的历史宿怨、地缘博弈、能源经济或教派矛盾，讲透为什么会在此时爆发。
4. 硬核细节与战术深潜：
   - 若涉及新武器/装备：深入拆解性能参数（航速、射程、制导方式、突防概率）、战术优劣势及实战功效；
   - 若涉及演习/冲突：剖析具体演练科目、针对的战区方向与潜在威慑对象；
   - 若涉及外交论坛或表态：剖析各方声明的字面措辞与背后潜台词。
5. 结构化对比表格：列出关键指标对比（如双方战力对比、性能参数表或战损筹码表）。
6. 局势洞见研判：从大国博弈与未来三个月走势，给出客观、冷峻的趋势研判。
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
