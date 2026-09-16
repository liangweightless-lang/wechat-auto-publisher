# -*- coding: utf-8 -*-
"""
移动端消息推送模块
职责：在文章生成完毕并推送到微信草稿箱后，将结果实时推送到手机端，支持 PushPlus、Server酱 和企业微信群机器人。
"""

import requests
from typing import Optional
from config.settings import settings, logger


class Notifier:
    """手机端状态通知推送器"""

    @staticmethod
    def send_pushplus(title: str, content_html: str) -> bool:
        """
        通过 PushPlus 推送加 发送手机微信通知
        用户在手机微信关注 PushPlus 公众号即可直接收到卡片通知
        """
        if not settings.PUSHPLUS_TOKEN:
            return False

        url = "http://www.pushplus.plus/send"
        payload = {
            "token": settings.PUSHPLUS_TOKEN,
            "title": title,
            "content": content_html,
            "template": "html"
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get("code") == 200:
                logger.info("手机微信通知发送成功 (PushPlus)")
                return True
            else:
                logger.warning(f"PushPlus 推送返回异常: {data.get('msg')}")
        except Exception as e:
            logger.error(f"PushPlus 推送网络失败: {e}")
        return False

    @staticmethod
    def send_serverchan(title: str, desp: str) -> bool:
        """
        通过 Server酱 发送手机微信通知
        """
        if not settings.SERVERCHAN_KEY:
            return False

        url = f"https://sctapi.ftqq.com/{settings.SERVERCHAN_KEY}.send"
        payload = {
            "title": title,
            "desp": desp
        }
        try:
            resp = requests.post(url, data=payload, timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                logger.info("手机微信通知发送成功 (Server酱)")
                return True
            else:
                logger.warning(f"Server酱 推送返回异常: {data.get('message')}")
        except Exception as e:
            logger.error(f"Server酱 推送网络失败: {e}")
        return False

    @staticmethod
    def send_wechat_work(markdown_text: str) -> bool:
        """
        向企业微信群机器人推送消息
        """
        if not settings.WECHAT_WORK_WEBHOOK:
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": markdown_text
            }
        }
        try:
            resp = requests.post(settings.WECHAT_WORK_WEBHOOK, json=payload, timeout=10)
            data = resp.json()
            if data.get("errcode") == 0:
                logger.info("企业微信群通知发送成功")
                return True
            else:
                logger.warning(f"企业微信推送失败: {data.get('errmsg')}")
        except Exception as e:
            logger.error(f"企业微信推送网络失败: {e}")
        return False

    @classmethod
    def notify_publish_success(cls, article_title: str, digest: str, media_id: str):
        """
        触发多渠道综合通知：发布到草稿箱成功
        """
        title = f"📢【局势洞见】今日草稿已就绪：{article_title[:20]}"
        body_html = f"""
        <div style="font-family: sans-serif; line-height: 1.6;">
            <h3 style="color: #1a365d;">今日舆情洞见文章已成功写入微信草稿箱</h3>
            <p><strong>文章标题：</strong>{article_title}</p>
            <p><strong>核心摘要：</strong>{digest}</p>
            <p><strong>草稿 Media ID：</strong><code>{media_id}</code></p>
            <p style="color: #2b6cb0; font-size: 13px;">
                💡 提示：您现在可以打开手机「订阅号助手」App，或登录微信公众平台后台，直接进行预览或一键群发。
            </p>
        </div>
        """
        # 尝试通过配置的通知渠道发送
        sent = False
        if cls.send_pushplus(title, body_html):
            sent = True
        if cls.send_serverchan(title, f"### {article_title}\n\n{digest}\n\n请前往手机微信订阅号助手一键发布。"):
            sent = True
        if cls.send_wechat_work(f"### 📢 今日微信文章已入草稿箱\n> **标题**：{article_title}\n> **摘要**：{digest}\n> 请在手机订阅号助手点击群发。"):
            sent = True

        if not sent:
            logger.info("未配置任何移动端通知渠道（PushPlus/Server酱），已跳过手机提醒。")
