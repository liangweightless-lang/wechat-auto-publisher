# -*- coding: utf-8 -*-
"""
微信公众号自动化发布系统 - 模块化服务启动入口 (App & Web Gateway)
职责：
1. 启动 HTTP 守护进程；
2. 调度 server.AppAPIHandler 处理 RESTful API 与静态文件分发；
3. 为后续原生 App、小程序及 Web 控制台提供统一入口。
"""

import sys
from http.server import HTTPServer
from config.settings import settings, logger
from server import AppAPIHandler

PORT = 8080


def run():
    """启动服务端"""
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, AppAPIHandler)
    logger.info("==================================================")
    logger.info("🛡️ 局势洞见 模块化发布服务已启动 (App & Web API Ready)")
    logger.info(f"👉 本地访问: http://localhost:{PORT}")
    logger.info(f"👉 云服务器公网访问: http://<云服务器公网IP>:{PORT}")
    logger.info(f"👉 移动 App/前端 API 基础路径: http://<公网IP>:{PORT}/api")
    logger.info("==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("发布服务已安全停止。")
        sys.exit(0)


if __name__ == '__main__':
    run()
