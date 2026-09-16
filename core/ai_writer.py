# -*- coding: utf-8 -*-
"""
AI 深度改写与智库分析引擎模块
职责：
1. 构建强去AI化、冷峻专业的防务与地缘博弈 Prompt；
2. 追求极高信息密度，字数精准控制在 1600~2200 字黄金篇幅（绝不冗长水字数）；
3. 重视权威官方通报/公告依据，包含态势数据看板表格、硬核参数对抗与情景推演；
4. 严格执行前置与后置合规风控审查（确保零敏感词、坚决不妄议中国自身）；
5. 产出高质量结构化 JSON：标题、摘要、精美 Markdown 正文。
"""

import json
import re
import requests
from typing import Dict, Any, Tuple
from config.settings import settings, logger


class AIWriter:
    """深度智库分析与公众号文章生成器"""

    # 深度去AI化的系统提示词
    SYSTEM_PROMPT = """你是一名长期从事国际防务、官方战报剖析、地缘战略与装备研究的资深首席分析员。文风与深度对标《白昃研究》《华山穹剑》以及国家安全智库专题研判。

【核心写作哲学与篇幅控制】：
1. **彻底摒除任何 AI 腔与口水废话**：
   - 严禁出现“总而言之”、“综上所述”、“犹如一柄双刃剑”、“在这个瞬息万变的时代”、“穿透迷雾”、“不可否认的是”、“值得我们深思”、“掀起惊涛骇浪”等空洞套话。
   - 行文必须冷峻、克制、硬核、事实第一。全篇多用专有名词、技术参数、地理坐标和博弈逻辑。
2. **字数严格控制在 1600 ~ 2200 字黄金篇幅（绝不水字数、追求极高信息密度）**：
   - 字数不是越多越好，拒绝冗长车轱辘话，每一句都必须交代硬核事实、官方公报依据、技术指标或深层动机。
3. **重视官方公告与战况公报的第一信源依据**：
   - 引述各方官方声明、军方发言人公报（如美军中央司令部CENTCOM、俄国防部每日战报、乌总参谋部、也门胡塞武装发言人、沙特国防部等）的具体通报细节作为研判抓手。
4. **黄金标题法则**：
   - 标题不超过 30 字，极具张力与权威感，直接点出官方通报背后的核心矛盾或关键逆转（例如：《官方战报背后的红海死结：胡塞导弹突防与美军护航的真实损耗》《间谍船遭袭真相：谁在曼德海峡扼住航道咽喉？》《沙特“2030愿景”的安全死穴：十年战火为何熄不灭？》）。
5. **绝对不可逾越的政治与合规红线（极重要）**：
   - **严禁妄议中国自身**：全文视角必须 100% 聚焦于外部当事各方（美军、胡塞武装、沙特、伊朗、以色列、北约、欧洲等）的战术撕扯、攻防死结与内部矛盾。
   - **严禁擅自揣测、臆造或分析中国政府、中方外交与国防决策背后的所谓“真实算盘”、“利益软肋”、“刚性诉求”或“幕后筹码/杠杆”**。绝不允许将中国作为下场博弈方进行动机剖析！
   - 坚决反驳西方涉华武器装备抹黑谣言，维护中国国家形象与利益。

【文章立体架构标准（必须完整紧凑呈现以下 5 大模块）】：
1. **【导读】**：3行以内的极简核心判决，直接交代官方公告的核心要点与当前战局不可逆拐点。
2. **## 01 官方通报复盘与核心态势看板**：
   - **必须包含一个标准的 Markdown 数据看板表格**（必须有表头和至少4行紧凑数据），梳理交火坐标、参战主力兵团、主战武器代际、单次攻防成本核算、航运/原油指数异动。
   - 结合官方战报，精细复盘突袭与拦截过程，指出雷达探测低空盲区与时序细节。
3. **## 02 硬核武器与攻防矛与盾较量**：
   - 列出具体武器装备型号与技术参数（突防马赫数、雷达反射截面 RCS、拦截过载包线、单发造价与效费比不对称计算，如 400 万美元标准-2 对阵 2 万美元廉价无人机）。
4. **## 03 地缘深水区与当事方现实死结**：
   - 结合战史与政治沿革，剖析当事国国内深层利益困境（如沙特2030愿景对招商和平的渴求 vs 胡塞武装对内统治合法性，美航母护航联盟多国出工不出力的现实撕扯）。
   - （切记：不得分析中国自身）。
5. **## 04 战略情景推演与未来走向模型**：
   - 严谨精炼给出三种未来推演模型：
     - **情景 A（基线概率 60%）**：低烈度常态化消耗战，护航与保费僵持；
     - **情景 B（升级概率 25%）**：战火外溢冲击周边油田管线与咽喉海峡；
     - **情景 C（暗室概率 15%）**：外部当事方达成非正式默契停火。
"""

    USER_PROMPT_TEMPLATE = """请基于以下官方公告或参考素材，撰写一篇 1600 ~ 2200 字之间、信息密度极高、去AI化的专业防务智库分析文章。

【官方通报/素材核心内容】：
{raw_content}

【特定焦点/补充指引】：
{user_focus}

【强制输出格式】：
必须以纯 JSON 格式输出，不要包含 ```json 或 ``` 包裹，直接输出最外层为花括号的合法 JSON：
{{
  "title": "文章主标题（不超过30字，抓眼球且严谨，拒绝口水）",
  "digest": "文章摘要（不超过60字，用于微信图文分享描述）",
  "markdown_content": "完整的正文内容（篇幅严控在 1600~2200 字黄金区间，包含【导读】、01官方通报复盘与数据看板表格、02硬核武器攻防、03地缘现实死结、04战略情景推演）"
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
        logger.info(f"正在调度 AI 智库模型生成 1600~2200 字深度长文 (模型: {self.model})...")

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
