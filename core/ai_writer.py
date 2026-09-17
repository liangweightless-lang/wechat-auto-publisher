from core.db import DatabaseManager
from core.prompt_manager import PromptManager
import os
import json
import re
import requests
from typing import Dict, Any, Tuple, Generator
from dotenv import load_dotenv
from config.settings import settings, logger
from core.historical_retriever import HistoricalRetriever
from core.formatter import WeChatFormatter

load_dotenv()


class AIWriter:
    """深度智库分析与公众号长文生成器 (DeepSeek-R1 深度思考 + 战史档案 RAG + 流式推送)"""

    SYSTEM_PROMPT = """你是一名长期从事国际防务、战史复盘与武器军工溯源研究的资深首席军事战略作家（文风对标《白昃研究》《华山穹剑》万字深度智库长文）。

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

    USER_PROMPT_TEMPLATE = """【当前突发/待研判战局线索】：
{raw_content}

-------------------------
【权威战史与军械库历史档案（请深度结合并引用分析）】：
{historical_dossier}

-------------------------
【用户定向关注与深度诉求】：
{user_focus}

请结合上述历史档案，以深度防务智库首席专家的专业笔触，展开透彻分析。请直接输出 Markdown（首行 # 标题，次行 > 摘要，随后正文与兵器谱表格）："""

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-R1")
        self.retriever = HistoricalRetriever()
        self.formatter = WeChatFormatter()

    def _check_compliance(self, text: str) -> Tuple[bool, str]:
        """政治与风控合规审查"""
        banned_phrases = [
            "中国的算盘", "中方的软肋", "中国的外交筹码", "中方在暗中布局",
            "中国幕后支持", "大疆光电", "中国零件支持"
        ]
        for phrase in banned_phrases:
            if phrase in text:
                return False, f"触发合规风控红线短语: '{phrase}'，严禁在研判中妄议中方立场或在军工溯源中关联中国！"
        return True, ""

    def _clean_content(self, text: str) -> str:
        """清理偶发的涉华造谣用词保底"""
        replacements = {
            "中国大疆": "西方黑市商用民用",
            "大疆精灵": "商用多旋翼民用",
            "中国制造": "国际黑市流通零部件",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    def generate_article_stream(self, raw_content: str, user_focus: str = "") -> Generator[Dict[str, Any], None, None]:
        """流式生成文章（同时捕获 DeepSeek-R1 的深度思考流与正文流）"""
        # 1. 历史资料 RAG 检索
        yield {"type": "status", "data": "正在检索全球地缘战史与武器库历史档案..."}
        historical_docs = self.retriever.retrieve(query=f"{raw_content} {user_focus}", top_k=5)
        historical_dossier = self.retriever.format_for_prompt(historical_docs)
        yield {"type": "status", "data": f"战史检索完成，已提取 {len(historical_docs)} 份底层战史与军械溯源档案。"}

        # 2. 构建 Prompt (从 PromptManager 动态获取最新配置)
        prompts = PromptManager.get_prompts()
        system_prompt = prompts.get("system_prompt", self.SYSTEM_PROMPT)
        user_template = prompts.get("user_prompt_template", self.USER_PROMPT_TEMPLATE)

        user_prompt = user_template.format(
            raw_content=raw_content[:8000],
            historical_dossier=historical_dossier,
            user_focus=user_focus or "全面结合历史材料，讲透双方为什么干起来的前因后果，并深扒双方动用武器的幕后国家技术血统与军工利益链。"
        )

        # 实时获取前端后台动态配置的大模型凭证与端点 (热生效，无需重启)
        llm_cfg = DatabaseManager.get_llm_config()
        active_api_key = llm_cfg["api_key"]
        active_base_url = llm_cfg["base_url"]
        active_model = llm_cfg["model"]

        headers = {
            "Authorization": f"Bearer {active_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 8192,
            "stream": True
        }

        url = f"{active_base_url.rstrip('/')}/chat/completions"
        yield {"type": "status", "data": f"正在连接 AI 推理集群 ({active_model})，启动深度战局推演..."}

        full_thinking = []
        full_content = []

        try:
            resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=180)
            if resp.status_code != 200:
                if resp.status_code == 402 or "insufficient" in resp.text.lower():
                    err_msg = "⚠️ 硅基流动(SiliconFlow) AI推理账户余额已耗尽 (HTTP 402)。请前往控制台 (cloud.siliconflow.cn) 充值，或在 .env 中更换有额度的 LLM_API_KEY 后重试。"
                elif resp.status_code == 401:
                    err_msg = "⚠️ AI 推理密钥无效或已过期 (HTTP 401 Unauthorized)。请检查 .env 文件中的 LLM_API_KEY 配置。"
                else:
                    err_msg = f"AI 推理集群响应异常: HTTP {resp.status_code} - {resp.text}"
                logger.error(err_msg)
                yield {"type": "error", "data": err_msg}
                return

            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode('utf-8')
                if not decoded.startswith('data: '):
                    continue
                raw_data = decoded[6:].strip()
                if raw_data == '[DONE]':
                    break

                try:
                    chunk = json.loads(raw_data)
                    delta = chunk['choices'][0]['delta']

                    # 捕获 DeepSeek-R1 思考流 (reasoning_content)
                    if 'reasoning_content' in delta and delta['reasoning_content']:
                        r_token = delta['reasoning_content']
                        full_thinking.append(r_token)
                        yield {"type": "think", "data": r_token}

                    # 捕获 正文生成流 (content)
                    if 'content' in delta and delta['content']:
                        c_token = delta['content']
                        full_content.append(c_token)
                        yield {"type": "content", "data": c_token}
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"流式生成网络异常: {e}")
            yield {"type": "error", "data": str(e)}
            return

        complete_md = "".join(full_content).strip()
        # 清洗可能出现的敏感违规
        complete_md = self._clean_content(complete_md)

        # 3. 解析标题与摘要
        title = "深度防务研判专栏"
        digest = "观察全球防务与地缘博弈。不跟风，不站队，只看事实与底层逻辑。"

        lines = complete_md.split(chr(10))
        remaining_lines = []
        for line in lines:
            if not title or title == "深度防务研判专栏":
                title_match = re.match(r'^#\s+(.+)$', line.strip())
                if title_match:
                    title = title_match.group(1).strip()
                    continue
            if not digest or digest.startswith("观察全球防务"):
                digest_match = re.match(r'^>\s*摘要[：:]\s*(.+)$', line.strip())
                if digest_match:
                    digest = digest_match.group(1).strip()
                    continue
            remaining_lines.append(line)

        markdown_body = chr(10).join(remaining_lines).strip()
        if not markdown_body:
            markdown_body = complete_md

        # 4. 转换为精美微信排版 HTML
        try:
            html_content = self.formatter.format_markdown(markdown_body)
        except Exception as e:
            logger.warning(f"排版格式化失败，使用原生转换: {e}")
            html_content = f"<div style='line-height: 1.75; font-size: 15px;'>{markdown_body}</div>"

        # 5. 推送最终完成事件
        result = {
            "title": title,
            "digest": digest,
            "markdown_content": complete_md,
            "body_content": markdown_body,
            "html_content": html_content,
            "thinking": "".join(full_thinking)
        }
        yield {"type": "done", "data": result}

    def generate_article(self, raw_content: str, user_focus: str = "") -> Dict[str, Any]:
        """向后兼容的同步调用方法"""
        final_result = None
        for evt in self.generate_article_stream(raw_content, user_focus):
            if evt["type"] == "done":
                final_result = evt["data"]
            elif evt["type"] == "error":
                raise RuntimeError(evt["data"])
        if not final_result:
            raise RuntimeError("未能成功生成文章内容")
        return final_result
