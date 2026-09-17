# -*- coding: utf-8 -*-
"""
AI 智库策略总监与动态抓取雷达引擎 (AI Strategist & Dynamic Radar)
职责：
1. 管理 storage/intelligence_strategy.json 配置（持久化存储用户调优出的抓取雷达、关键词、思考侧重与排版偏好）；
2. 支持与用户像豆包/ChatGPT 一样多轮对话，动态解析用户调整意图，自动更新抓取关键词与提示词策略；
3. 支持根据每日全球焦点，由 AI 自动推演今日防务突发关键词雷达。
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

from config.settings import settings, logger


class StrategyManager:
    """策略持久化与状态管理"""
    STRATEGY_FILE = Path(__file__).resolve().parent.parent / "storage" / "intelligence_strategy.json"

    DEFAULT_STRATEGY = {
        "version": "1.0",
        "last_updated": "2026-09-17",
        "focus_summary": "全面覆盖中东以伊冲突、俄乌前线交锋、红海护航以及台海南海等四大垂直体系防务动态。",
        "active_keywords": [
            "高超音速", "饱和打击", "防空反导", "防区外", "雷达盲区", 
            "电子战", "无人机蜂群", "巡航导弹", "洲际导弹", "核潜艇"
        ],
        "custom_clusters": [],
        "analysis_style": "强调真实官方信源、战术技术指标深度对比、多波次突防推演，杜绝AI空话套话，结构化标头对齐。",
        "display_preferences": {
            "show_original_en_title": True,
            "highlight_official_badge": True,
            "default_theme": "think_tank"
        },
        "chat_history": [
            {
                "role": "assistant",
                "content": "您好！我是您的防务智库策略总监。您可以随时告诉我今天的关注重点（例如：'今天重点追踪也门胡塞对美军航母的电子干扰战术'，或'把文章标题改得更具智库研判风格'），我会为您实时调整抓取雷达词库和研报生成偏好！"
            }
        ]
    }

    @classmethod
    def load_strategy(cls) -> Dict[str, Any]:
        """读取策略配置，若不存在则初始化默认配置"""
        if cls.STRATEGY_FILE.exists():
            try:
                with open(cls.STRATEGY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 补充缺失字段
                    for k, v in cls.DEFAULT_STRATEGY.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception as e:
                logger.error(f"读取策略文件失败: {e}，使用默认配置")
        cls.save_strategy(cls.DEFAULT_STRATEGY)
        return cls.DEFAULT_STRATEGY.copy()

    @classmethod
    def save_strategy(cls, strategy: Dict[str, Any]):
        """持久化保存策略"""
        cls.STRATEGY_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cls.STRATEGY_FILE, "w", encoding="utf-8") as f:
                json.dump(strategy, f, ensure_ascii=False, indent=2)
            logger.info("✅ 智库策略配置已持久化更新")
        except Exception as e:
            logger.error(f"保存策略文件异常: {e}")

    @classmethod
    def get_active_keywords(cls) -> List[str]:
        """获取当前活跃的动态关键词列表"""
        strategy = cls.load_strategy()
        return strategy.get("active_keywords", [])


class AIStrategist:
    """AI 策略调优引擎 (支持与用户交互式持续迭代)"""

    @classmethod
    def chat_tune(cls, user_message: str) -> Dict[str, Any]:
        """
        与用户对话并自动解析调优意图，联动更新策略配置。
        返回：{"reply": str, "strategy": dict, "updated_fields": list}
        """
        current_strategy = StrategyManager.load_strategy()
        history = current_strategy.get("chat_history", [])

        # 追加用户发言
        history.append({"role": "user", "content": user_message})
        # 保持最近10轮对话
        history = history[-12:]

        system_prompt = (
            "你是资深防务智库策略总监与总编辑。用户正在与你沟通今日的防务情报抓取思路、选题重点与微信长文风格偏好。\n"
            "你的任务是：\n"
            "1. 给出专业、自信、富有洞察力的中文回复，解答用户并汇报你做出的具体策略调整；\n"
            "2. 在回复末尾附带严格的 ```json 格式块，输出根据用户意图更新的配置字段（如果没有改动则保持原样）：\n"
            "```json\n"
            "{\n"
            '  "focus_summary": "今日重点一句话概括",\n'
            '  "add_keywords": ["新增加的防务/武器/地缘雷达关键词"],\n'
            '  "remove_keywords": ["移除的关键词"],\n'
            '  "analysis_style": "文章写作偏好与战法侧重描述"\n'
            "}\n"
            "```"
        )

        api_key = settings.LLM_API_KEY
        base_url = settings.LLM_BASE_URL.rstrip("/")

        # 组装对话消息
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        assistant_reply = "已收到您的策略指示，已为您优化抓取雷达与研报侧重点！"
        json_delta = {}

        # 优先使用 Qwen2.5-7B 秒级响应，备用 DeepSeek-V3
        for model in ["Qwen/Qwen2.5-7B-Instruct", "deepseek-ai/DeepSeek-V3"]:
            try:
                resp = requests.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 800
                    },
                    timeout=15,
                    verify=False
                )
                if resp.status_code == 200:
                    raw_content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    # 提取 json 块
                    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_content, re.DOTALL)
                    if json_match:
                        try:
                            json_delta = json.loads(json_match.group(1))
                            assistant_reply = raw_content[:json_match.start()].strip()
                        except Exception:
                            assistant_reply = raw_content.strip()
                    else:
                        assistant_reply = raw_content.strip()
                    break
            except Exception as e:
                logger.warning(f"策略对话调用模型 {model} 异常: {e}")

        # 应用差异到策略
        updated_fields = []
        if json_delta:
            if "focus_summary" in json_delta and json_delta["focus_summary"]:
                current_strategy["focus_summary"] = json_delta["focus_summary"]
                updated_fields.append("focus_summary")

            if "add_keywords" in json_delta and isinstance(json_delta["add_keywords"], list):
                existing_kw = set(current_strategy.get("active_keywords", []))
                for kw in json_delta["add_keywords"]:
                    if kw and kw not in existing_kw:
                        existing_kw.add(kw)
                        updated_fields.append(f"+关键词:{kw}")
                current_strategy["active_keywords"] = list(existing_kw)

            if "remove_keywords" in json_delta and isinstance(json_delta["remove_keywords"], list):
                existing_kw = set(current_strategy.get("active_keywords", []))
                for kw in json_delta["remove_keywords"]:
                    if kw in existing_kw:
                        existing_kw.remove(kw)
                        updated_fields.append(f"-关键词:{kw}")
                current_strategy["active_keywords"] = list(existing_kw)

            if "analysis_style" in json_delta and json_delta["analysis_style"]:
                current_strategy["analysis_style"] = json_delta["analysis_style"]
                updated_fields.append("analysis_style")

        # 记录 AI 回复到历史
        history.append({"role": "assistant", "content": assistant_reply})
        current_strategy["chat_history"] = history
        current_strategy["last_updated"] = time.strftime("%Y-%m-%d %H:%M")

        StrategyManager.save_strategy(current_strategy)

        return {
            "reply": assistant_reply,
            "strategy": current_strategy,
            "updated_fields": updated_fields
        }

    @classmethod
    def refresh_daily_radar(cls, recent_news_titles: List[str] = None) -> List[str]:
        """
        基于近期国际动态与战报线索，AI 自动提炼今天最关键的 8-12 个防务雷达词
        """
        api_key = settings.LLM_API_KEY
        base_url = settings.LLM_BASE_URL.rstrip("/")
        titles_sample = "\n".join(recent_news_titles[:15]) if recent_news_titles else "暂无样本新闻"

        prompt = (
            f"以下是今日国际前沿一手防务报道标题摘要：\n{titles_sample}\n\n"
            "请基于第一性原理与当前国际战局关键交锋，推演今日最应该重点追踪抓取的 8-10 个'核心防务高频实体与武器战术词'。\n"
            "要求：输出 JSON 字符串数组，例如：[\"库尔斯克反突击\", \"低空巡飞弹\", \"佩列亚斯拉夫\", \"萨德反导\", \"红海护航\"]，不要额外文字。"
        )

        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 300
                },
                timeout=12,
                verify=False
            )
            if resp.status_code == 200:
                out = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                m = re.search(r"\[.*?\]", out, re.DOTALL)
                if m:
                    keywords = json.loads(m.group(0))
                    if isinstance(keywords, list) and len(keywords) > 0:
                        strategy = StrategyManager.load_strategy()
                        current_kws = set(strategy.get("active_keywords", []))
                        current_kws.update(keywords)
                        strategy["active_keywords"] = list(current_kws)
                        StrategyManager.save_strategy(strategy)
                        logger.info(f"AI 成功更新今日雷达关键词: {keywords}")
                        return list(current_kws)
        except Exception as e:
            logger.warning(f"AI 刷新今日雷达异常: {e}")

        return StrategyManager.get_active_keywords()
