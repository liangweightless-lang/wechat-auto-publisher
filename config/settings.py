# -*- coding: utf-8 -*-
"""
全局配置与风控规则模块
职责：加载环境变量，管理微信接口、大模型凭证，并定义前置敏感词与合规安全策略。
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 定位项目根目录并加载 .env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # 尝试加载父级或系统环境变量
    load_dotenv()

# 企业通用日志目录配置
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = "%(asctime)s - [%(levelname)s] - [%(name)s]: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("WeChatPublisher")


class Settings:
    """系统全局运行时配置类"""

    # 微信公众平台凭据
    WECHAT_APPID: str = os.getenv("WECHAT_APPID", "").strip()
    WECHAT_APPSECRET: str = os.getenv("WECHAT_APPSECRET", "").strip()
    WECHAT_DEFAULT_AUTHOR: str = os.getenv("WECHAT_DEFAULT_AUTHOR", "舆情洞见").strip()

    # 大模型 API 配置 (支持兼容 OpenAI 接口规范的各类模型)
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "").strip()
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat").strip()

    # 移动端通知配置
    PUSHPLUS_TOKEN: str = os.getenv("PUSHPLUS_TOKEN", "").strip()
    SERVERCHAN_KEY: str = os.getenv("SERVERCHAN_KEY", "").strip()
    WECHAT_WORK_WEBHOOK: str = os.getenv("WECHAT_WORK_WEBHOOK", "").strip()

    # 安全合规审查规则（严守国家安全底线）
    # 严禁涉及危害国家统一、领土完整、攻击党和政府体制、传播境内涉政违规谣言等内容
    SENSITIVE_KEYWORDS = [
        # 此处维护前置拦截的黑名单词根（可根据业务需要随时扩充）
        "分裂国家", "颠覆政权", "反动谣言", "暴乱煽动", "泄露国家军事机密"
    ]

    @classmethod
    def validate_wechat_credentials(cls) -> bool:
        """检查微信必要凭证是否已正确配置"""
        if not cls.WECHAT_APPID or not cls.WECHAT_APPSECRET:
            logger.error("未检测到有效 WECHAT_APPID 或 WECHAT_APPSECRET，请检查 .env 配置文件！")
            return False
        return True


settings = Settings()
