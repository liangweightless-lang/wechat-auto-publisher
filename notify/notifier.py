# -*- coding: utf-8 -*-
"""
移动端消息推送模块
职责：在文章生成完毕并推送到微信草稿箱后，将结果实时推送到手机端（PushPlus/Server酱）。
企业规范：企业微信机器人消息已按需暂时注释，避免打扰群内同事。
"""

import requests
from typing import Optional
from config.settings import settings, logger


class Notifier:
    """移动端消息通知中心"""

    @staticmethod
    def send_pushplus(title: str, content: str) -> bool:
        """
        通过 PushPlus 推送加 发送个人手机微信通知
        用户在手机微信关注 PushPlus 公众号即可直接收到卡片通知
        """
        if not settings.PUSHPLUS_TOKEN:
            return False

        url = "http://www.pushplus.plus/send"
        payload = {
            "token": settings.PUSHPLUS_TOKEN,
            "title": title,
            "content": content,
            "template": "html" if "<" in content else "txt"
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
        """通过 Server酱 发送手机微信通知"""
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
        【暂时注释】按企业通用规范与指令，暂时禁用向企业微信群发消息，避免打扰群内同事
        """
        # =========================================================================
        # [暂缓启用] 如后续需要企业微信群机器人，解除以下注释即可：
        #
        # if not settings.WECHAT_WORK_WEBHOOK:
        #     return False
        # payload = {
        #     "msgtype": "markdown",
        #     "markdown": {"content": markdown_text}
        # }
        # try:
        #     resp = requests.post(settings.WECHAT_WORK_WEBHOOK, json=payload, timeout=10)
        #     if resp.json().get("errcode") == 0:
        #         logger.info("企业微信群通知发送成功")
        #         return True
        # except Exception as e:
        #     logger.error(f"企业微信推送失败: {e}")
        # =========================================================================
        logger.info("企业微信群通知当前处于暂时停用/注释状态，已跳过发送。")
        return False

    @classmethod
    def send_all(cls, title: str, content: str):
        """
        通用多通道通知入口
        """
        # 1. 优先尝试 PushPlus 个人通知
        if cls.send_pushplus(title, content):
            return True

        # 2. 备用 Server酱
        if cls.send_serverchan(title, content):
            return True

        # 3. 企业微信群（当前处于注释状态）
        # cls.send_wechat_work(content)

        return False

    @classmethod
    def notify_publish_success(cls, article_title: str, digest: str, media_id: str):
        """发布到微信草稿箱成功的通知"""
        title = f"📢【局势洞见】今日草稿已就绪：{article_title[:20]}"
        body_text = f"文章标题：{article_title}\n摘要：{digest}\nMedia ID：{media_id}\n\n请在手机「订阅号助手」App 中审核群发！"
        cls.send_all(title, body_text)
