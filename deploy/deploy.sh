#!/usr/bin/env bash
# ==============================================================================
# 腾讯云服务器 (TencentOS / Ubuntu / CentOS) 一键初始化部署脚本
# 适用：微信公众号自动化内容生成系统
# ==============================================================================

set -e

echo ">>> [1/5] 开始检测系统环境与依赖..."

# 检查 Python 3
if ! command -v python3 &>/dev/null; then
    echo "未检测到 Python 3，正在尝试自动安装基础工具..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv git
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3 python3-pip git
    else
        echo "错误：请手动安装 Python 3.9+ 环境后再运行本脚本！"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "当前 Python 版本: ${PYTHON_VERSION}"

# 定位项目根目录
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${APP_DIR}"

echo ">>> [2/5] 创建并初始化 Python 独立虚拟环境 (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo ">>> [3/5] 升级 pip 并安装项目核心依赖..."
pip install --upgrade pip -i https://mirrors.tencent.com/pypi/simple/
pip install -r requirements.txt -i https://mirrors.tencent.com/pypi/simple/

echo ">>> [4/5] 检查环境变量配置文件..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️ 已自动从 .env.example 生成 .env 配置文件！"
    echo "👉 请立即执行: vim ${APP_DIR}/.env"
    echo "👉 填入您的 WECHAT_APPID、WECHAT_APPSECRET 和 LLM_API_KEY。"
else
    echo ".env 配置文件已存在，跳过初始化。"
fi

echo ">>> [5/5] 获取当前腾讯云服务器外网 IP..."
PUBLIC_IP=$(curl -s https://api.ipify.org || curl -s https://ip.sb || echo "无法自动获取")
echo "=================================================================="
echo "🎉 腾讯云服务器基础环境部署完成！"
echo "📌 当前云服务器公网 IP 为: ${PUBLIC_IP}"
echo "⚠️ 请确保已将该公网 IP 添加到微信开发者平台的「IP 白名单」中！"
echo "📌 项目运行目录: ${APP_DIR}"
echo "=================================================================="
echo "测试运行示例："
echo "  source venv/bin/activate"
echo "  1. 启动可视化 Web 网页控制台 (推荐):"
echo "     nohup ./venv/bin/python main.py --web > web.log 2>&1 &"
echo "     浏览器访问: http://${PUBLIC_IP}:8080"
echo ""
echo "  2. 命令行快速处理:"
echo "     python main.py --file '/path/to/report.pdf'"
echo "=================================================================="
