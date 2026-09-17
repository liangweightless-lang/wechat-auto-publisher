# -*- coding: utf-8 -*-
"""
微信公众号官方 API 客户端模块
职责：
1. 管理 Access Token 凭据生命周期与本地缓存续期；
2. 上传永久图片素材（作为文章封面需要的 thumb_media_id）；
3. 上传文章内部引用的图片到腾讯 CDN；
4. 将排版好的 HTML 图文推送到微信公众平台草稿箱。
"""

import time
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from config.settings import settings, logger


class WeChatAPIError(Exception):
    """微信接口调用通用异常"""
    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"[WeChat API Error {errcode}] {errmsg}")


class WeChatClient:
    """微信公众号 API 交互客户端"""

    BASE_URL = "https://api.weixin.qq.com/cgi-bin"

    def __init__(self):
        self.appid = settings.WECHAT_APPID
        self.appsecret = settings.WECHAT_APPSECRET
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取或刷新微信公众平台 Access Token
        机制：本地内存缓存，并在过期前 5 分钟（300秒）自动静默刷新
        """
        current_time = time.time()
        if not force_refresh and self._access_token and current_time < (self._token_expires_at - 300):
            return self._access_token

        if not self.appid or not self.appsecret:
            raise ValueError("微信 AppID 或 AppSecret 未配置，请先在 .env 中正确填写！")

        url = f"{self.BASE_URL}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret
        }

        logger.info("正在向微信服务器请求刷新 Access Token...")
        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
        except Exception as e:
            logger.error(f"连接微信服务器失败: {e}")
            raise

        if "errcode" in data and data["errcode"] != 0:
            errcode = data["errcode"]
            errmsg = data.get("errmsg", "")
            if errcode == 40164:
                # 微信特定的 IP 未加白名单错误
                logger.critical(
                    f"【微信 IP 白名单拦截】微信提示当前机器 IP 不在白名单内！\n"
                    f"微信返回信息: {errmsg}\n"
                    f"请务必在微信开发者平台将当前外网 IP 加入白名单后重试。"
                )
            raise WeChatAPIError(errcode, errmsg)

        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 7200)
        self._token_expires_at = current_time + expires_in
        logger.info(f"Access Token 获取成功，有效时长: {expires_in} 秒")
        return self._access_token

    def upload_thumb_material(self, image_path: str) -> str:
        """
        上传永久图片素材，作为草稿箱文章的封面图
        :param image_path: 本地图片文件的绝对路径或相对路径
        :return: media_id (草稿图文封面所需的 thumb_media_id)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"封面图片文件不存在: {image_path}")

        token = self.get_access_token()
        url = f"{self.BASE_URL}/material/add_material?access_token={token}&type=image"

        logger.info(f"正在上传永久封面素材: {path.name} ...")
        with open(path, "rb") as f:
            files = {"media": (path.name, f, "image/jpeg")}
            resp = requests.post(url, files=files, timeout=30)
            data = resp.json()

        if "errcode" in data and data["errcode"] != 0:
            raise WeChatAPIError(data["errcode"], data.get("errmsg", "素材上传失败"))

        media_id = data["media_id"]
        logger.info(f"封面图片素材上传成功，media_id: {media_id}")
        return media_id

    def upload_content_image(self, image_path: str) -> str:
        """
        上传图文消息内引用的图片，获取微信 CDN 永久外链
        （草稿 HTML 正文中的图片必须是腾讯自身 CDN 链接，防盗链机制拦截外部非微信图片）
        :param image_path: 本地图片路径
        :return: 微信 CDN 图片 URL
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"正文图片文件不存在: {image_path}")

        token = self.get_access_token()
        url = f"{self.BASE_URL}/media/uploadimg?access_token={token}"

        logger.info(f"正在上传正文内嵌图片: {path.name} ...")
        with open(path, "rb") as f:
            files = {"media": (path.name, f, "image/jpeg")}
            resp = requests.post(url, files=files, timeout=30)
            data = resp.json()

        if "errcode" in data and data["errcode"] != 0:
            raise WeChatAPIError(data["errcode"], data.get("errmsg", "正文图片上传失败"))

        cdn_url = data["url"]
        logger.info(f"正文图片转存微信 CDN 成功: {cdn_url}")
        return cdn_url

    def create_draft(
        self,
        title: str,
        content_html: str,
        thumb_media_id: str,
        author: str = "",
        digest: str = "",
        content_source_url: str = ""
    ) -> str:
        """
        提交图文内容到公众号草稿箱 (Draft Box)
        :param title: 文章标题 (不超过 64 字)
        :param content_html: 带内联 CSS 样式的微信富文本 HTML 正文
        :param thumb_media_id: 封面图的 media_id
        :param author: 作者署名 (如 '局势洞见')
        :param digest: 图文摘要 (若留空微信会自动截取正文前段)
        :param content_source_url: 原文阅读链接（可选）
        :return: 创建成功的草稿 media_id
        """
        token = self.get_access_token()
        url = f"{self.BASE_URL}/draft/add?access_token={token}"

        if not author:
            author = settings.WECHAT_DEFAULT_AUTHOR

        article_item = {
            "title": title[:64],
            "author": author[:16],
            "digest": digest[:120],
            "content": content_html,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,        # 开启留言（如有权限）
            "only_fans_can_comment": 0
        }

        if content_source_url:
            article_item["content_source_url"] = content_source_url

        payload = {
            "articles": [article_item]
        }

        logger.info(f"正在向微信草稿箱推送文章：《{title}》...")
        # 必须确保 json 序列化以 utf-8 传输中文，微信服务器才不会乱码
        resp = requests.post(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30
        )
        data = resp.json()

        if "errcode" in data and data["errcode"] != 0:
            raise WeChatAPIError(data["errcode"], data.get("errmsg", "草稿保存失败"))

        draft_media_id = data.get("media_id", "")
        logger.info(f"🎉 文章已成功录入微信公众号草稿箱！Draft Media ID: {draft_media_id}")
        return draft_media_id

    def upload_permanent_material(self, file_path: str, material_type: str = "image") -> str:
        """别名兼容方法"""
        return self.upload_thumb_material(file_path)

    def add_draft(self, articles: list) -> str:
        """别名兼容方法 (支持 articles 列表格式)"""
        if not articles:
            raise ValueError("articles 列表不能为空")
        art = articles[0]
        return self.create_draft(
            title=art.get("title", "未命名"),
            content_html=art.get("content", ""),
            thumb_media_id=art.get("thumb_media_id", ""),
            author=art.get("author", ""),
            digest=art.get("digest", "")
        )
