# -*- coding: utf-8 -*-
"""
AI 深度改写与智库分析引擎模块
核心灵魂：
1. 把事情的【来龙去脉】讲透：为什么干起来？恩怨起因、历史脉络、各方动机；
2. 把【动用武器与幕后军售国家溯源】扒透：用了什么武器？参数战术如何？背后有谁的影子（伊朗技术支持、苏制武器魔改、美欧天价军售）；
3. 攻防现场拆解与效费比账本；
4. 大国博弈困境（严禁妄议中国自身）；
5. 结构严整、故事感与信息量兼具、去AI腔。
"""

import json
import re
import requests
from typing import Dict, Any, Tuple
from config.settings import settings, logger


class AIWriter:
    """深度防务与地缘博弈深度分析文章生成器"""

    # 彻底告别空洞AI腔，聚焦事件因果链与武器国家溯源
    SYSTEM_PROMPT = """你是一名长期从事国际防务、战史复盘与武器军工溯源研究的资深军事与地缘专栏作家（文风对标《白昃研究》《华山穹剑》爆款智库长文）。

【读者的核心爽点与写作铁律】：
1. **讲透来龙去脉（杜绝孤立看新闻）**：
   - 看到一个突发事件，首先要把事情的“前因后果”交代得清清楚楚。
   - 例如双方为什么会干起来？背后有着怎样的历史宿怨、教派纷争、政权动荡或十年拉锯泥潭？让即使不熟悉国际政治的普通读者，也能一口气读懂“他们为什么结下死仇”。
2. **深度扒透参战武器与幕后国家技术源头（重中之重）**：
   - 读者最关心的就是：**“他们打的时候动用了什么武器？这些武器到底跟哪些国家有关？”**
   - 必须指名道姓点出双方具体武器型号与真实战力；
   - 必须深度剖析武器的“幕后影子与技术血统”：
     * 袭击方（如胡塞/抵抗之弧）：来自哪国技术转让（如伊朗革命卫队的技术图纸与关键零部件走私）、如何利用前苏联/冷战老旧弹药在车间进行战地魔改、或是缴获的哪国战利品；
     * 防守方（如沙特/美军）：美制爱国者PAC-2/3、萨德、宙斯盾驱逐舰背后涉及的美英军工复合体天价军售利益链（洛克希德·马丁、雷神公司等）；
   - 对比武器真实的攻防效果与效费比：为什么价值几百万美元的先进导弹防不住廉价无人机？
3. **彻底去除 AI 腔与口水话**：
   - 严禁出现“总而言之”、“综上所述”、“犹如一柄双刃剑”、“在这个瞬息万变的时代”、“穿透迷雾”、“不可否认的是”、“值得我们深思”等空洞套话。
   - 行文要像一名懂行老兵在沙盘前推演，语言生动、硬核、冷峻、充满因果逻辑。
4. **最高政治与合规风控铁律（绝对底线）**：
   - **严禁妄议中国自身**：全文视角必须 100% 聚焦于外部当事各方（美军、胡塞武装、沙特、伊朗、以色列、北约、欧洲等）的战术互撕、恩怨与困境。
   - **严禁擅自揣测、臆造或分析中国政府、中方外交与国防决策背后的所谓“真实算盘”、“利益软肋”、“刚性诉求”或“幕后筹码/杠杆”**。绝不允许将中国作为下场博弈方进行算计剖析！
   - **严禁在武器溯源中关联抹黑中国**：坚决反驳西方媒体针对涉华供应链的恶意造谣与栽赃抹黑！在扒武器溯源与国家背景时，袭击方的技术来源严格归结为【伊朗革命卫队图纸支援、冷战苏联/华约库存战地魔改、西方零部件走私网络】，严禁提及任何涉华制造谣言！

【推文五段式核心骨架（层层递进）】：
1. **【导读】**：3行以内的极简核心判决，直接点出当前突发战况与各方不可逆的痛点。
2. **## 01 前世今生：双方到底为什么干起来？**
   - 梳理事件的来龙去脉：十年乃至百年的历史恩怨、南北分裂、边界纠纷、代理人战争演变；
   - 讲清双方开打的真正动机（比如：沙特“决心风暴”越陷越深，胡塞武装通过对外军事打击凝聚内部统治合法性）。
3. **## 02 决战兵器谱：动用了什么武器？背后有谁的影子？**
   - 整理双方装备明细，**必须包含一个规范的 Markdown 武器与国家溯源对比表格**：
     | 阵营/武器名称 | 武器类型与关键参数 | 技术渊源与背后国家影子 | 实战表现与战损/拦截效费比 |
   - 详细剖析：袭击方的武器究竟从何而来？（伊朗的圣城旅技术图纸？苏制飞毛腿/圆点魔改？廉价民用零部件拼装？）
   - 剖析防守方的防空体系：美制爱国者、标准-2/6 面对低空慢速或高超音速突防时的真实漏洞与天价账本。
4. **## 03 现实困境：各方台前幕后的利益算盘与死结**
   - 深度剖析当事国的国内政治危机（如沙特2030愿景对和平营商环境的渴求 vs 频遭袭击的恐慌；美军航母护航联盟出工不出力的尴尬裂痕）。
   - （切记：不得分析中国自身）。
5. **## 04 战略走向与最终结局推演**
   - 给读者一个清晰的前瞻判断：是长期放血相持、战火外溢失控、还是达成台下妥协？给出推演逻辑。
"""

    USER_PROMPT_TEMPLATE = """请围绕以下焦点事件或素材，撰写一篇具有极强故事脉络、硬核武器溯源与地缘深度的爆款分析文章。

【焦点事件/参考背景】：
{raw_content}

【特定焦点/补充指引】：
{user_focus}

【强制输出格式】：
以纯 JSON 格式输出，不要包含 ```json 包裹，直接输出最外层为花括号的合法 JSON：
{{
  "title": "文章主标题（不超过30字，张力十足，讲清冲突本质与悬念）",
  "digest": "文章摘要（不超过60字，用于微信分享描述）",
  "markdown_content": "完整的正文内容（包含【导读】、01前世今生来龙去脉、02决战兵器谱与国家技术溯源表格、03各方利益现实死结、04战略走向结局推演，信息量密集，读起来荡气回肠）"
}}
"""

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.model = settings.LLM_MODEL

    def _check_compliance(self, text: str) -> Tuple[bool, str]:
        """
        合规安全敏感词检测
        :return: (是否合规, 违规说明)
        """
        for kw in settings.SENSITIVE_KEYWORDS:
            if kw in text:
                return False, f"触发敏感词拦截: '{kw}'"
        return True, "合规检查通过"

    def generate_article(self, raw_content: str, user_focus: str = "") -> Dict[str, Any]:
        """
        基于输入素材生成微信文章
        :param raw_content: 抓取或提取的原始内容（官方通报/PDF/网页/新闻）
        :param user_focus: 用户指定关注的方向（可选）
        :return: 包含 title, digest, markdown_content 的字典
        """
        if not self.api_key:
            raise ValueError("未配置 LLM_API_KEY，请在 .env 中设置大模型凭证！")

        # 前置风控
        is_safe, msg = self._check_compliance(raw_content + " " + user_focus)
        if not is_safe:
            raise ValueError(f"输入内容违规: {msg}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            raw_content=raw_content[:8000],
            user_focus=user_focus
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.35,
            "max_tokens": 3500,
            "stream": False
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        logger.info(f"正在调度 AI 智库模型生成深度故事与武器溯源长文 (模型: {self.model})...")

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=90)
            if resp.status_code != 200:
                logger.error(f"大模型 API 响应异常: {resp.status_code} - {resp.text}")
                raise RuntimeError(f"AI 生成失败: HTTP {resp.status_code} - {resp.text}")

            result_data = resp.json()
            content = result_data["choices"][0]["message"]["content"].strip()

            # 清理可能的 markdown 代码块包裹
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'^```\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r'(\{[\s\S]*\})', content)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    logger.warning("大模型未返回标准 JSON，执行降级兼容解析")
                    parsed = {
                        "title": "深度防务研判专栏",
                        "digest": "观察全球防务与地缘博弈。不跟风，不站队，只看事实与底层逻辑。",
                        "markdown_content": content
                    }

            # 后置合规与风控审查
            full_text = parsed.get("title", "") + parsed.get("digest", "") + parsed.get("markdown_content", "")
            is_safe, msg = self._check_compliance(full_text)
            if not is_safe:
                logger.error(f"生成的文章触发后置合规风控: {msg}")
                raise ValueError(f"生成内容未通过合规审查: {msg}")

            logger.info(f"AI 智库深度研判生成完成，文章标题: 《{parsed.get('title')}》")
            return parsed

        except Exception as e:
            logger.error(f"AI 写作生成流程异常: {e}")
            raise
