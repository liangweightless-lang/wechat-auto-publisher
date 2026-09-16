# -*- coding: utf-8 -*-
"""
AI 深度改写与智库分析引擎模块
职责：
1. 构建强去AI化、冷峻专业的防务与地缘博弈 Prompt；
2. 调度大语言模型（兼容 OpenAI / DeepSeek / Kimi / 阿里等协议）；
3. 执行前置与后置合规风控审查（确保零敏感词、符合国家立场）；
4. 产出结构化结果：标题、摘要、精美 Markdown 正文。
"""

import json
import re
import requests
from typing import Dict, Any, Tuple
from config.settings import settings, logger


class AIWriter:
    """深度智库分析与公众号文章生成器"""

    # 深度去AI化的系统提示词
    SYSTEM_PROMPT = """你是一名长期从事国际防务、地缘战略与国家安全研究的资深分析员（文风对标《白昃研究》《华山穹剑》）。
你的写作原则：
1. **彻底去除 AI 腔**：严禁出现“总而言之”、“综上所述”、“犹如一柄双刃剑”、“在这个瞬息万变的时代”、“穿透迷雾”、“引人深思”等空洞口水话。
2. **文风冷峻、客观、克制**：只摆事实、数据、装备型号、战术推演和台前幕后的实际利益博弈，不煽情、不迎合、不打鸡血。
3. **黄金标题标准**：短促有力、有悬念或关键数据、揭示深层矛盾（例如：《45天从威慑到实战：美军在红海的真正困境》《间谍船遭袭真相：谁在曼德海峡扼住咽喉？》）。
4. **严格合规底线**：坚决遵守中国国家安全法与主流立场。严禁出现任何危害国家统一、攻击中国党政体制或未经证实的涉华负面谣言。对国际事件进行冷静客观的学术/智库剖析。
5. **四段式结构**：
   - 【导读】：3行以内的极简核心研判。
   - ## 01 全景复盘（发生了什么，关键节点与时间线）
   - ## 02 技术与战术博弈（武器装备、战术对抗、攻防成本差异）
   - ## 03 利益深层穿透（各参与方的政治算盘与现实困境）
   - ## 04 战略启示与走向（未来演变趋势与地缘影响）
"""

    USER_PROMPT_TEMPLATE = """请基于以下提供的参考素材，撰写一篇具有深度战略穿透力的公众号专栏分析文章。

【参考素材/报告核心内容】：
{raw_content}

【特定焦点/补充要求】：
{user_focus}

【输出要求】：
请务必以严格的 JSON 格式输出，不要附加任何额外的 markdown 标记外面包裹（格式如下）：
{{
  "title": "文章主标题（不超过30字，抓眼球且严谨）",
  "digest": "文章摘要（不超过60字，用于微信分享描述）",
  "markdown_content": "完整的正文内容（遵循四段式结构，包含导读和01/02/03/04标题）"
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

        # 1. 前置合规审查
        passed, msg = self._check_compliance(raw_content[:2000])
        if not passed:
            raise ValueError(f"输入素材未通过前置安全审查: {msg}")

        # 截取适度长度防止上下文爆满（保留前 12000 字）
        truncated_content = raw_content[:12000]

        logger.info(f"正在调用大模型 ({self.model}) 进行深度改写与排版结构化...")
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            raw_content=truncated_content,
            user_focus=user_focus or "围绕核心冲突背后的防务技术与利益博弈深入拆解"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4,  # 低随机度保证专业严谨
            "response_format": {"type": "json_object"}
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=90)
            data = resp.json()
        except Exception as e:
            logger.error(f"请求大模型 API 异常: {e}")
            raise

        if "error" in data:
            raise RuntimeError(f"大模型返回错误: {data['error']}")

        raw_reply = data["choices"][0]["message"]["content"]

        # 解析 JSON
        try:
            # 去除可能包含的 ```json 代码块外壳
            cleaned_json_str = re.sub(r'^```json\s*', '', raw_reply.strip())
            cleaned_json_str = re.sub(r'\s*```$', '', cleaned_json_str)
            result = json.loads(cleaned_json_str)
        except Exception as e:
            logger.error(f"解析大模型返回的 JSON 失败，返回原始内容: {raw_reply[:300]}")
            raise ValueError(f"大模型未输出标准 JSON: {e}")

        # 2. 后置合规审查生成的正文和标题
        full_generated_text = f"{result.get('title', '')} {result.get('markdown_content', '')}"
        passed, msg = self._check_compliance(full_generated_text)
        if not passed:
            raise ValueError(f"生成的内容触发安全风控拦截: {msg}")

        logger.info(f"文章生成成功！标题：《{result.get('title')}》")
        return result
