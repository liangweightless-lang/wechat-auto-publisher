# 微信公众号自动化智库研判与发布系统

专为“防务、地缘战略与重大舆情洞见”公众号量身定制的内容自动生成与微信草稿箱推送系统。

---

## 🌟 核心特性

- **严格去 AI 化文风**：杜绝口水套话（拒绝“总而言之”、“犹如双刃剑”、“穿透迷雾”等空洞表述），文风对标《白昃研究》《华山穹剑》，冷静、克制、严谨、只摆数据与利益推演。
- **微信专属高级排版**：内置专为微信设计的 **Inline CSS 渲染引擎**，生成深海蓝与钛金灰质感的主题卡片、金句引用块、章节胶囊、数据强调盒，视觉高级。
- **坚守安全合规红线**：双重敏感词与安全机制，严格符合国家立场与合规要求。
- **官方草稿箱无缝对接**：自动维护 Access Token 并上传素材，一键推送至微信公众号后台草稿箱。
- **手机端实时监控与一键发布**：支持推送通知到手机微信（PushPlus / Server酱），配合微信官方 **「订阅号助手」App**，在手机端即可直接预览并一键群发。
- **腾讯云一键部署**：内置一键安装与 Linux 定时任务（Crontab）调度脚本。

---

## 📂 工程结构

```
wechat-auto-publisher/
├── .env.example              # 环境变量配置模板（微信凭据、大模型配置、推送Key）
├── requirements.txt          # Python 核心依赖库
├── README.md                 # 完整使用说明文档
├── deploy/                   # 云端运维配置
│   ├── deploy.sh             # 腾讯云 Linux 服务器一键部署安装脚本
│   └── crontab.example       # 每日定时无人值守任务配置样例
├── config/                   # 配置层
│   └── settings.py           # 全局环境加载与合规安全审查规则
├── core/                     # 核心业务引擎
│   ├── wechat_api.py         # 微信官方公众平台 API 封装（Token、素材、草稿）
│   ├── content_parser.py     # 多源素材提取（PDF 智库报告提取、网页长文清洗）
│   ├── ai_writer.py          # 深度智库分析改写引擎
│   ├── formatter.py          # 微信图文内联 CSS 高端排版渲染器
│   └── cover_generator.py    # 微信 2.35:1 官方比例封面图自动生成
├── notify/                   # 手机端通知层
│   └── notifier.py           # 微信消息推送（PushPlus / Server酱 / 企微机器人）
└── main.py                   # 统一控制台入口（CLI）
```

---

## 🚀 快速上手（本地运行）

### 1. 安装依赖
```bash
cd wechat-auto-publisher
pip install -r requirements.txt
```

### 2. 配置环境变量
复制模板生成 `.env` 文件：
```bash
cp .env.example .env
```
用编辑器打开 `.env` 填入您的微信凭证与大模型密钥：
```ini
WECHAT_APPID=您的微信公众号AppID
WECHAT_APPSECRET=您的微信公众号AppSecret
WECHAT_DEFAULT_AUTHOR=局势洞见

# 大模型 API (支持 DeepSeek / Kimi / OpenAI / 阿里百炼 等兼容接口)
LLM_API_KEY=sk-xxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 可选：手机微信通知 (http://www.pushplus.plus/)
PUSHPLUS_TOKEN=
```

### 3. 本地调试与效果预览 (Dry-Run 模式)
在不调用微信上传接口的前提下，查看生成的文章与排版：
```bash
# 依据热点话题生成并在本地预览：
python main.py --topic "美军间谍船遭袭事件深度复盘" --dry-run
```
> 执行后会在 `scratch/preview.html` 生成网页文件，双击可用浏览器直接预览微信真实排版效果。

### 4. 正式推送到微信公众号草稿箱
确保微信开发者平台已将当前 IP 加入白名单：
```bash
# 从本地 PDF 报告生成（如聊天记录中提到的报告）：
python main.py --file "/path/to/胡塞武装与沙特冲突舆情报告_20260916.pdf"

# 或直接围绕热点撰写并发布：
python main.py --topic "胡塞武装控制曼德海峡的地缘博弈"
```

---

## ☁️ 部署到腾讯云服务器指南

### 1. 将项目代码上传到云服务器
```bash
# 在云服务器的目标目录下拉取或通过 scp 上传代码
scp -r wechat-auto-publisher root@<您的腾讯云服务器IP>:/root/
```

### 2. 执行一键安装脚本
登录腾讯云服务器终端，运行部署脚本：
```bash
cd /root/wechat-auto-publisher
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```
> 脚本会自动安装 Python 依赖，并在终端末尾打印该云服务器的**外网固定 IP**。

### 3. 配置微信公众号 IP 白名单
将上一步打印的腾讯云公网 IP，复制到 **微信开发者平台 -> 接口管理 -> IP 白名单** 中保存。

### 4. 设置 7×24 小时无人值守定时发布 (Crontab)
编辑定时任务：
```bash
crontab -e
```
添加如下定时规则（例如每天早晨 07:30 自动执行一次）：
```bash
30 7 * * * cd /root/wechat-auto-publisher && ./venv/bin/python main.py --topic "全球重点防务热点与地缘博弈" >> /root/wechat-auto-publisher/cron.log 2>&1
```

---

## 📱 手机端操作工作流

1. **自动推送**：程序在云端每天早晨定时完成抓取与草稿推送。
2. **手机提醒**：您的手机微信会收到一条 PushPlus 卡片通知（显示文章标题与摘要）。
3. **手机一键发布**：打开微信官方 **「订阅号助手」App**，进入草稿箱，点击“发表”，即可完成当日推送。
