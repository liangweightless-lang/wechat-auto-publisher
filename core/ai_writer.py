# -*- coding: utf-8 -*-
"""
AI 深度改写与智库分析引擎模块
职责：
1. 构建强去AI化、冷峻专业的防务与地缘博弈 Prompt；
2. 对标 10 页专业智库报告与《白昃研究》《华山穹剑》深度万字级架构；
3. 输出 2500~3500 字扎实长文，包含结构化核心数据看板表格、硬核攻防拆解与情景推演；
4. 执行严密的前置与后置合规风控审查（确保零敏感词、坚决不妄议中国自身）；
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
    SYSTEM_PROMPT = """你是一名长期从事国际防务、武器装备、地缘战略与大国博弈研究的资深首席分析员。文风与深度对标《白昃研究》《华山穹剑》以及国家安全智库专题舆情报告。

【核心写作哲学与文风规范】：
1. **彻底摒除任何 AI 腔与口水废话**：
   - 严禁出现“总而言之”、“综上所述”、“犹如一柄双刃剑”、“在这个瞬息万变的时代”、“穿透迷雾”、“不可否认的是”、“值得我们深思”、“掀起惊涛骇浪”等空洞套话。
   - 行文必须冷峻、克制、硬核、事实第一。全篇多用短句、专有名词、技术参数、地理坐标和博弈逻辑。
2. **拒绝蜻蜓点水的新闻摘要，必须输出 2500 ~ 3500 字的智库级深度长文**：
   - 必须深入到底层装备型号、雷达制导机制、效费比财务账本、部族教派地缘恩怨和各方国内政治死结。
3. **黄金标题法则**：
   - 标题不超过 30 字，极具张力与专业感，揭示矛盾内核或关键转折（例如：《45天从威慑到实战：美军在红海的真正死结》《间谍船遭袭真相：谁在曼德海峡扼住航道咽喉？》《沙特“2030愿景”的安全死穴：也门十年战火为何熄不灭？》）。
4. **绝对不可逾越的政治与合规红线（极重要）**：
   - **严禁妄议中国自身**：全文视角必须 100% 聚焦于外部当事各方（美军、胡塞武装、沙特、伊朗、以色列、北约、欧洲等）的战术撕扯、攻防死结与内部矛盾。
   - **严禁擅自揣测、臆造或分析中国政府、中方外交与国防决策背后的所谓“真实算盘”、“利益软肋”、“刚性诉求”或“幕后筹码/杠杆”**。绝不允许将中国作为下场博弈方进行动机剖析！
   - 严禁借题发挥危害中国国家利益与形象，坚决反驳西方针对中国涉军涉防务的无端抹黑与谣言。

【文章立体架构标准（必须完整呈现以下 6 大模块）】：
1. **【导读】**：4行以内的极简硬核核心判断，直接亮明当前局势的关键拐点与不可逆趋势。
2. **## 01 战局复盘与核心态势看板**：
   - **必须包含一个标准的 Markdown 数据看板表格**（必须有表头和至少4行数据），对比交火区域坐标、对阵双方核心主力、武器代际差异、战损/拦截效费比、原油现货与航运费率指数异动。
   - 紧接着详细复盘袭击或交火过程，还原低空防空盲区、无人机与巡航导弹突防时序路径。
3. **## 02 硬核武器与战术攻防矛与盾较量**：
   - 列出具体武器装备型号与技术参数（如高超音速反舰导弹突防速度与末端机动、自杀式无人机飞行高度与雷达反射面积、宙斯盾雷达视场盲区、近防炮热过载瓶颈）。
   - 计算真实战场效费比（如单枚 400 万美元的“标准-2/6”拦截 2 万美元廉价无人机的消耗账本，美军垂直发射系统 VLS 弹药再装填困境）。
4. **## 03 地缘深水区与百年历史宿怨**：
   - 挖掘历史沿革与地缘死结（如也门南北分裂、也门萨达省宰德派复兴、沙特“决心风暴”十年泥潭）。
   - 剖析当事国国内政治深层逻辑（沙特王储萨勒曼“2030愿景”对招商引资安全环境的极度依赖 vs 胡塞武装通过对外强硬凝聚国内统治合法性的刚性需求）。
5. **## 04 战略困境穿透与当事方内部撕扯**：
   - 剖析美军航母打击群进退失据的战略尴尬、“繁荣卫士”多国护航联盟各怀鬼胎出工不出力的现实裂痕。
   - （切记：不得分析中国自身，视角严格限定在外部各当事方）。
6. **## 05 战略情景推演与未来走向模型**：
   - 严谨给出三种推演模型：
     - **情景 A（基线概率 60%）**：低烈度常态化消耗战，航运持续绕行好望角；
     - **情景 B（升级概率 25%）**：战火外溢冲击关键输油管线与霍尔木兹海峡；
     - **情景 C（妥协概率 15%）**：外部当事各方通过暗室外交达成脆弱默契停火。
"""

    USER_PROMPT_TEMPLATE = """请基于以下参考素材或焦点话题，撰写一篇 2500 ~ 3500 字具有极致战略穿透力、专业硬核的防务智库分析长文。

【参考素材/报告核心背景】：
{raw_content}

【特定焦点/补充指引】：
{user_focus}

【强制输出格式】：
必须以纯 JSON 格式输出，不要包含 ```json 或 ``` 包裹，直接输出最外层为花括号的合法 JSON：
{{
  "title": "文章主标题（不超过30字，抓眼球且严谨，拒绝口水）",
  "digest": "文章摘要（不超过60字，用于微信图文分享描述）",
  "markdown_content": "完整的正文内容（必须包含【导读】、01态势数据看板表格、02硬核武器攻防矛与盾、03百年地缘历史宿怨、04当事方困境撕扯、05三种战略情景推演，字数在2500~3500字之间）"
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
        :param raw_content: 抓取或提取的原始内容（PDF/网页/新闻）
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
            raw_content=raw_content[:8000],  # 扩大输入承载力
            user_focus=user_focus
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.35,
            "max_tokens": 4096,
            "stream": False
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        logger.info(f"正在调度 AI 智库模型生成深度长文 (模型: {self.model})...")

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
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
                # 尝试用正则提取 json 结构
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

            logger.info(f"AI 智库深度分析生成完成，文章标题: 《{parsed.get('title')}》")
            return parsed

        except Exception as e:
            logger.error(f"AI 写作生成流程异常: {e}")
            raise
