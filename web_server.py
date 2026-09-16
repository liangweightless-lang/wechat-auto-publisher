# -*- coding: utf-8 -*-
"""
微信公众号自动化发布系统 - 移动端主流自媒体工作台
"""

import os
import json
import cgi
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from config.settings import settings, logger
from core import WeChatClient, ContentParser, AIWriter, WeChatFormatter, CoverGenerator, ImageService, DefenseCrawler
from notify import Notifier

PORT = 8080
BASE_DIR = Path(__file__).resolve().parent

# 临时内存缓存上一次生成的内容
CURRENT_CACHE = {
    "title": "",
    "digest": "",
    "html_content": "",
    "markdown_content": "",
    "cover_image": "",
    "thumb_media_id": "",
    "word_count": 0,
    "read_time": 0
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>局势洞见 · 微信公众号创作工作台</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* ================= 1. 市面主流自媒体双主题设计规范 ================= */
        :root {
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --bg-card-sub: #f1f5f9;
            --border: #e2e8f0;
            --border-hover: #cbd5e1;
            --text-title: #0f172a;
            --text-body: #334155;
            --text-muted: #64748b;
            --text-light: #94a3b8;
            --primary: #1e40af;
            --primary-hover: #1d4ed8;
            --primary-soft: #eff6ff;
            --wechat: #07c160;
            --wechat-hover: #06ad56;
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
            --shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
            --badge-hot: #ef4444;
            --badge-official: #2563eb;
        }

        [data-theme="dark"] {
            --bg-page: #0b0f19;
            --bg-card: #131b2e;
            --bg-card-sub: #1e293b;
            --border: #26334d;
            --border-hover: #3b4d70;
            --text-title: #f8fafc;
            --text-body: #cbd5e1;
            --text-muted: #94a3b8;
            --text-light: #64748b;
            --primary: #3b82f6;
            --primary-hover: #60a5fa;
            --primary-soft: rgba(59, 130, 246, 0.12);
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
            --shadow-lg: 0 12px 30px rgba(0, 0, 0, 0.6);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background-color: var(--bg-page);
            color: var(--text-body);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding-bottom: calc(85px + env(safe-area-inset-bottom));
            transition: background-color 0.25s ease, color 0.25s ease;
        }

        /* 顶部品牌导航栏 */
        .app-header {
            position: sticky;
            top: 0;
            z-index: 50;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
        }
        .header-brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-logo {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 17px;
            font-weight: 700;
        }
        .brand-text {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-title);
            letter-spacing: 0.3px;
        }
        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .theme-toggle-btn {
            background: var(--bg-card-sub);
            border: 1px solid var(--border);
            color: var(--text-muted);
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
        }

        /* 分段控制器导航 */
        .nav-segment-container {
            max-width: 680px;
            margin: 12px auto 6px auto;
            padding: 0 16px;
            width: 100%;
        }
        .nav-segment {
            background: var(--bg-card-sub);
            border: 1px solid var(--border);
            padding: 3px;
            border-radius: 10px;
            display: flex;
        }
        .segment-btn {
            flex: 1;
            padding: 9px 0;
            text-align: center;
            font-size: 13.5px;
            font-weight: 600;
            color: var(--text-muted);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            user-select: none;
        }
        .segment-btn.active {
            background: var(--bg-card);
            color: var(--text-title);
            box-shadow: var(--shadow-sm);
        }
        .dot-badge {
            width: 6px;
            height: 6px;
            background: var(--wechat);
            border-radius: 50%;
            display: none;
        }

        /* 主体视图 */
        .view-pane { display: none; max-width: 680px; margin: 0 auto; padding: 12px 16px; width: 100%; }
        .view-pane.active { display: block; }

        /* 卡片容器 */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: var(--shadow-sm);
            transition: box-shadow 0.2s, border-color 0.2s;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .card-title {
            font-size: 14px;
            font-weight: 700;
            color: var(--text-title);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .card-subtext {
            font-size: 12px;
            color: var(--text-muted);
            cursor: pointer;
        }

        /* 极简上传框 */
        .upload-box {
            background: var(--bg-card-sub);
            border: 1.5px dashed var(--border);
            border-radius: 12px;
            padding: 18px 14px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .upload-box:hover { border-color: var(--primary); background: var(--primary-soft); }
        .upload-box-title { font-size: 13.5px; font-weight: 600; color: var(--text-title); }
        .upload-box-desc { font-size: 11.5px; color: var(--text-muted); }

        /* 滑动分类栏 */
        .tab-scroll-bar {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 12px;
            scrollbar-width: none;
            -webkit-overflow-scrolling: touch;
        }
        .tab-scroll-bar::-webkit-scrollbar { display: none; }
        .tab-chip {
            background: var(--bg-card-sub);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12.5px;
            font-weight: 500;
            white-space: nowrap;
            flex-shrink: 0;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab-chip.active {
            background: var(--primary);
            color: #ffffff;
            border-color: var(--primary);
            font-weight: 600;
        }

        /* 热搜排行榜式的情报列表 (对标主流资讯流) */
        .topic-list-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .topic-row-item {
            background: var(--bg-card-sub);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 14px;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }
        .topic-row-item:hover, .topic-row-item:active {
            border-color: var(--primary);
            background: var(--primary-soft);
            transform: translateY(-1px);
        }
        .topic-rank-num {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 15px;
            font-weight: 800;
            color: var(--text-light);
            min-width: 22px;
            text-align: center;
            line-height: 1.2;
            padding-top: 2px;
        }
        .topic-row-item:nth-child(1) .topic-rank-num { color: #ef4444; }
        .topic-row-item:nth-child(2) .topic-rank-num { color: #f97316; }
        .topic-row-item:nth-child(3) .topic-rank-num { color: #f59e0b; }

        .topic-main-content {
            flex: 1;
        }
        .topic-top-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }
        .topic-badge-tag {
            font-size: 10.5px;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 4px;
            background: rgba(30, 64, 175, 0.08);
            color: var(--primary);
            border: 1px solid rgba(30, 64, 175, 0.15);
        }
        .topic-origin { font-size: 11px; color: var(--text-muted); }
        .topic-headline {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-title);
            line-height: 1.45;
            margin-bottom: 4px;
        }
        .topic-abstract {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        /* 焦点多行输入框 */
        .focus-input-area {
            margin-top: 14px;
            border-top: 1px dashed var(--border);
            padding-top: 12px;
        }
        .focus-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .focus-title { font-size: 13px; font-weight: 700; color: var(--text-title); }
        .focus-clear {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 11.5px;
            cursor: pointer;
            padding: 2px 6px;
        }
        .focus-clear:hover { color: #ef4444; }

        .input-textarea {
            width: 100%;
            background: var(--bg-card-sub);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px;
            color: var(--text-title);
            font-size: 14px;
            line-height: 1.5;
            resize: none;
            outline: none;
            transition: all 0.2s;
            min-height: 72px;
        }
        .input-textarea:focus {
            border-color: var(--primary);
            background: var(--bg-card);
            box-shadow: 0 0 0 3px var(--primary-soft);
        }

        /* 核心生成大按钮 */
        .btn-start-generate {
            width: 100%;
            background: var(--primary);
            color: #ffffff;
            border: none;
            padding: 15px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: var(--shadow-md);
            transition: all 0.2s;
        }
        .btn-start-generate:active { transform: scale(0.99); background: var(--primary-hover); }

        /* 微信推文 1:1 仿真外框 */
        .preview-tool-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 12.5px;
        }
        .tool-btn {
            background: var(--bg-card-sub);
            border: 1px solid var(--border);
            color: var(--text-body);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
        }
        .tool-btn:hover { border-color: var(--primary); color: var(--primary); }

        /* 仿真 iPhone 微信文章阅读器 */
        .wechat-mock-container {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 24px 18px;
            color: #2d3748;
            box-shadow: var(--shadow-sm);
            min-height: 600px;
        }
        .mock-article-header {
            margin-bottom: 20px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 14px;
        }
        .mock-title {
            font-size: 21px;
            font-weight: 700;
            color: #1a202c;
            line-height: 1.4;
            margin-bottom: 12px;
        }
        .mock-author-row {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
        }
        .mock-author-name {
            color: #576b95;
            font-weight: 600;
            cursor: pointer;
        }
        .mock-time { color: #a0aec0; }

        /* 底部吸底微信推送大条 */
        .fixed-bottom-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 60;
            background: var(--bg-card);
            border-top: 1px solid var(--border);
            padding: 10px 16px calc(10px + env(safe-area-inset-bottom)) 16px;
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
            display: flex;
            justify-content: center;
        }
        .fixed-bottom-inner {
            max-width: 680px;
            width: 100%;
        }
        .btn-wechat-push {
            width: 100%;
            background: var(--wechat);
            color: #ffffff;
            border: none;
            padding: 14px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(7, 193, 96, 0.25);
            transition: all 0.2s;
        }
        .btn-wechat-push:active { background: var(--wechat-hover); transform: scale(0.99); }

        /* 旋转微指示器 */
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: #ffffff;
            border-radius: 50%;
            animation: spin 0.75s linear infinite;
            display: none;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* 思考步骤浮层 */
        .stepper-mask {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
            z-index: 200;
            align-items: center;
            justify-content: center;
            padding: 20px;
            pointer-events: none;
        }
        .stepper-mask.active {
            display: flex !important;
            pointer-events: auto !important;
        }
        .stepper-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            width: 100%;
            max-width: 380px;
            padding: 24px;
            box-shadow: var(--shadow-lg);
        }
        .stepper-title { font-size: 16px; font-weight: 700; color: var(--text-title); text-align: center; margin-bottom: 16px; }
        .stepper-line {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0;
            font-size: 13px;
            color: var(--text-muted);
        }
        .stepper-line.active { color: var(--primary); font-weight: 600; }
        .stepper-line.done { color: var(--wechat); }
        .step-circle {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 1.5px solid currentColor;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            flex-shrink: 0;
        }

        /* 居中 Toast */
        #toast {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 10px 20px;
            background: #0f172a;
            color: #ffffff;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 500;
            z-index: 999;
            display: none;
            box-shadow: var(--shadow-lg);
            border: 1px solid #334155;
            white-space: nowrap;
        }
    </style>
</head>
<body>

    <!-- 顶部原生式状态栏 -->
    <header class="app-header">
        <div class="header-brand">
            <div class="brand-logo">局</div>
            <div>
                <div class="brand-text">局势洞见</div>
            </div>
        </div>
        <div class="header-actions">
            <div class="theme-toggle-btn" onclick="toggleTheme()" title="切换日间/夜间模式">
                <span id="themeIcon">☀️</span>
            </div>
        </div>
    </header>

    <!-- 主流悬浮分段导航 -->
    <div class="nav-segment-container">
        <div class="nav-segment">
            <div class="segment-btn active" id="tabNavEdit" onclick="switchView('edit')">
                <span>🎯 选题与生成</span>
            </div>
            <div class="segment-btn" id="tabNavPreview" onclick="switchView('preview')">
                <span>📖 推文排版预览</span>
                <div class="dot-badge" id="previewDot"></div>
            </div>
        </div>
    </div>

    <!-- 1. 选题与生成视图 -->
    <div class="view-pane active" id="viewEdit">

        <!-- 报告/素材导入卡片 -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📁 智库报告 / 原始资料导入</div>
                <div class="card-subtext">支持 PDF / TXT</div>
            </div>
            <input type="file" id="mobileFileInput" accept=".pdf,.txt" style="display: none;" onchange="handleMobileFile(this)">
            <div class="upload-box" onclick="document.getElementById('mobileFileInput').click()">
                <div style="font-size: 24px;">📑</div>
                <div class="upload-box-title" id="mobileFileLabel">点击导入本地 PDF 智库报告</div>
                <div class="upload-box-desc">自动解析报告内容、数据图表与时间线</div>
            </div>
        </div>

        <!-- 多源情报榜单 (对标今日头条/新榜热搜流) -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">🌐 全球防务与官方公告榜</div>
                <div class="card-subtext" onclick="fetchHotTopics(activeCategory)" style="color: var(--primary);">
                    🔄 刷新榜单
                </div>
            </div>

            <!-- 分类滑动胶囊 -->
            <div class="tab-scroll-bar">
                <div class="tab-chip active" onclick="selectCategory('all', this)">全域热点</div>
                <div class="tab-chip" onclick="selectCategory('official', this)">🏛️ 官方战报公告</div>
                <div class="tab-chip" onclick="selectCategory('middle_east', this)">🔴 红海中东</div>
                <div class="tab-chip" onclick="selectCategory('eurasia', this)">🔵 俄乌欧亚</div>
                <div class="tab-chip" onclick="selectCategory('tech', this)">🟢 硬核战法</div>
                <div class="tab-chip" onclick="selectCategory('power', this)">🟡 大国海权</div>
                <div class="tab-chip" onclick="selectCategory('rolling', this)">⚡ 实时快报</div>
            </div>

            <!-- 动态热搜榜单列表 -->
            <div class="topic-list-group" id="mobileHotList">
                <div style="text-align: center; padding: 24px; font-size: 13px; color: var(--text-muted);">
                    正在拉取最新防务情报与官方通报...
                </div>
            </div>

            <!-- 研判输入区域 -->
            <div class="focus-input-area">
                <div class="focus-header">
                    <div class="focus-title">✍️ 焦点话题：</div>
                    <button type="button" class="focus-clear" onclick="clearTopicInput()">✕ 清空</button>
                </div>
                <textarea class="input-textarea" id="mobileTopicInput" rows="3"
                    oninput="autoResizeTextarea(this)"
                    placeholder="从上方榜单轻点选定，或直接输入焦点事件..."></textarea>
                <div id="charCount" style="text-align: right; font-size: 11px; color: var(--text-light); margin-top: 4px;">0 字</div>
            </div>
        </div>

        <!-- 启动生成大按钮 -->
        <button class="btn-start-generate" id="mobileGenBtn" onclick="triggerMobileGenerate()">
            <div class="spinner" id="mobileGenSpinner"></div>
            <span id="mobileGenText">🚀 开始深度研判并生成配图</span>
        </button>
    </div>

    <!-- 2. 仿真微信推文预览视图 -->
    <div class="view-pane" id="viewPreview">
        <div class="preview-tool-bar">
            <div>
                <span style="color: var(--text-muted);">状态: </span>
                <strong id="statWordCount" style="color: var(--primary);">待生成</strong>
            </div>
            <button class="tool-btn" onclick="copyWechatHtml()">
                📋 复制微信排版
            </button>
        </div>

        <!-- 仿真微信文章纸张容器 -->
        <div class="wechat-mock-container">
            <div class="mock-article-header">
                <div class="mock-title" id="previewMockTitle">文章标题待生成</div>
                <div class="mock-author-row">
                    <span class="mock-author-name">局势洞见</span>
                    <span style="color: #cbd5e1;">·</span>
                    <span style="color: #576b95;">原创</span>
                    <span style="color: #cbd5e1;">·</span>
                    <span class="mock-time" id="previewMockTime">今日</span>
                </div>
            </div>
            <div id="mobilePreviewContent">
                <div style="text-align: center; padding: 80px 20px; color: #94a3b8;">
                    <div style="font-size: 40px; margin-bottom: 12px;">📰</div>
                    <div style="font-weight: 600; font-size: 15px; color: #475569;">暂无生成内容</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 6px;">请在「选题与生成」中选定话题后点击生成</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 底部固定吸底栏 (微信经典排版) -->
    <div class="fixed-bottom-bar">
        <div class="fixed-bottom-inner">
            <button class="btn-wechat-push" id="mobilePublishBtn" onclick="triggerMobilePublish()">
                <div class="spinner" id="mobilePubSpinner"></div>
                <span id="mobilePubText">📤 一键推送到微信公众号草稿箱</span>
            </button>
        </div>
    </div>

    <!-- 进度弹层 -->
    <div class="stepper-mask" id="progressModal">
        <div class="stepper-box">
            <div class="stepper-title">研判生产引擎运转中</div>
            <div class="stepper-line" id="step1">
                <div class="step-circle">1</div>
                <div>官方战报交叉比对与前置风控</div>
            </div>
            <div class="stepper-line" id="step2">
                <div class="step-circle">2</div>
                <div>还原事件前世今生与冲突因果链</div>
            </div>
            <div class="stepper-line" id="step3">
                <div class="step-circle">3</div>
                <div>决战兵器谱与幕后国家技术溯源</div>
            </div>
            <div class="stepper-line" id="step4">
                <div class="step-circle">4</div>
                <div>快手可图生成 2.35:1 电影级战地大片</div>
            </div>
            <div class="stepper-line" id="step5">
                <div class="step-circle">5</div>
                <div>微信专属 Inline CSS 引擎排版装配</div>
            </div>
        </div>
    </div>

    <!-- 悬浮 Toast -->
    <div id="toast"></div>

    <script>
        let mobileSelectedFile = null;
        let activeCategory = 'all';

        // 切换浅色/深色模式
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const target = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', target);
            document.getElementById('themeIcon').innerText = target === 'dark' ? '🌙' : '☀️';
            localStorage.setItem('wechat_theme', target);
        }

        // 初始化加载主题偏好
        (function() {
            const saved = localStorage.getItem('wechat_theme') || 'light';
            document.documentElement.setAttribute('data-theme', saved);
            window.addEventListener('DOMContentLoaded', () => {
                const icon = document.getElementById('themeIcon');
                if (icon) icon.innerText = saved === 'dark' ? '🌙' : '☀️';
            });
        })();

        function showToast(msg, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.background = isError ? "#ef4444" : "#0f172a";
            t.style.display = "block";
            setTimeout(() => { t.style.display = "none"; }, 3000);
        }

        function switchView(viewName) {
            document.querySelectorAll('.view-pane').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.segment-btn').forEach(el => el.classList.remove('active'));

            if (viewName === 'edit') {
                document.getElementById('viewEdit').classList.add('active');
                document.getElementById('tabNavEdit').classList.add('active');
            } else {
                document.getElementById('viewPreview').classList.add('active');
                document.getElementById('tabNavPreview').classList.add('active');
                document.getElementById('previewDot').style.display = 'none';
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function handleMobileFile(input) {
            if (input.files.length) {
                mobileSelectedFile = input.files[0];
                document.getElementById('mobileFileLabel').innerText = "已就绪: " + mobileSelectedFile.name;
                document.getElementById('mobileFileLabel').style.color = "var(--primary)";
                showToast("已成功选定报告文件！");
            }
        }

        function selectCategory(cat, el) {
            activeCategory = cat;
            document.querySelectorAll('.tab-chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            fetchHotTopics(cat);
        }

        async function fetchHotTopics(cat = 'all') {
            const list = document.getElementById('mobileHotList');
            list.innerHTML = '<div style="text-align: center; padding: 24px; font-size: 13px; color: var(--text-muted);">正在拉取最新防务情报...</div>';
            try {
                const resp = await fetch(`/api/crawl?category=${cat}`);
                const data = await resp.json();
                if (data.code === 200 && data.topics.length) {
                    list.innerHTML = '';
                    data.topics.forEach((t, idx) => {
                        const item = document.createElement('div');
                        item.className = 'topic-row-item';
                        item.onclick = () => {
                            const inp = document.getElementById('mobileTopicInput');
                            inp.value = t.title;
                            autoResizeTextarea(inp);
                            showToast("已选定话题！");
                            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                        };
                        const rankNum = (idx + 1) < 10 ? '0' + (idx + 1) : (idx + 1);
                        item.innerHTML = `
                            <div class="topic-rank-num">${rankNum}</div>
                            <div class="topic-main-content">
                                <div class="topic-top-meta">
                                    <span class="topic-badge-tag">${t.level || t.keyword || '焦点'}</span>
                                    <span class="topic-origin">${t.source || '防务通报'}</span>
                                </div>
                                <div class="topic-headline">${t.title}</div>
                                <div class="topic-abstract">${t.summary || ''}</div>
                            </div>
                        `;
                        list.appendChild(item);
                    });
                } else {
                    list.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 24px; font-size: 12px;">暂无该分类动态，可直接输入研究话题</div>';
                }
            } catch (e) {
                list.innerHTML = '<div style="color: #ef4444; padding: 16px; font-size: 12px;">网络拉取异常: ' + e + '</div>';
            }
        }

        function updateStep(stepNum) {
            for (let i = 1; i <= 5; i++) {
                const el = document.getElementById('step' + i);
                el.classList.remove('active', 'done');
                if (i < stepNum) {
                    el.classList.add('done');
                    el.querySelector('.step-circle').innerText = '✓';
                } else if (i === stepNum) {
                    el.classList.add('active');
                    el.querySelector('.step-circle').innerText = i;
                } else {
                    el.querySelector('.step-circle').innerText = i;
                }
            }
        }

        function autoResizeTextarea(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.max(72, Math.min(textarea.scrollHeight, 200)) + 'px';
            const len = textarea.value.trim().length;
            const countEl = document.getElementById('charCount');
            if (countEl) countEl.innerText = len + ' 字';
        }

        function clearTopicInput() {
            const input = document.getElementById('mobileTopicInput');
            input.value = '';
            autoResizeTextarea(input);
            showToast("已清空输入框");
        }

        async function triggerMobileGenerate() {
            const topic = document.getElementById('mobileTopicInput').value.trim();
            if (!mobileSelectedFile && !topic) {
                showToast("⚠️ 请先点选上方话题或选择报告！", true);
                const inputEl = document.getElementById('mobileTopicInput');
                if (inputEl) { inputEl.focus(); }
                return;
            }

            const modal = document.getElementById('progressModal');
            modal.classList.add('active');
            updateStep(1);

            const timer1 = setTimeout(() => updateStep(2), 3500);
            const timer2 = setTimeout(() => updateStep(3), 8500);
            const timer3 = setTimeout(() => updateStep(4), 16000);
            const timer4 = setTimeout(() => updateStep(5), 23000);

            const formData = new FormData();
            if (mobileSelectedFile) formData.append("file", mobileSelectedFile);
            if (topic) formData.append("topic", topic);

            try {
                const resp = await fetch("/api/generate", { method: "POST", body: formData });
                const data = await resp.json();
                clearTimeout(timer1); clearTimeout(timer2); clearTimeout(timer3); clearTimeout(timer4);
                modal.classList.remove('active');

                if (data.code === 200) {
                    document.getElementById('mobilePreviewContent').innerHTML = data.html_content;
                    document.getElementById('previewMockTitle').innerText = data.title;
                    document.getElementById('previewDot').style.display = 'block';

                    const words = data.word_count || Math.round(data.html_content.length / 2);
                    document.getElementById('statWordCount').innerText = `${words.toLocaleString()} 字 · 约 ${Math.ceil(words / 400)} 分钟`;

                    showToast("🎉 推文排版与大片配图已就绪！");
                    setTimeout(() => { switchView('preview'); }, 400);
                } else {
                    showToast("生成失败: " + data.message, true);
                }
            } catch (err) {
                clearTimeout(timer1); clearTimeout(timer2); clearTimeout(timer3); clearTimeout(timer4);
                modal.classList.remove('active');
                showToast("网络连接异常: " + err, true);
            }
        }

        function copyWechatHtml() {
            const content = document.getElementById('mobilePreviewContent');
            if (!content || content.innerText.includes('暂无生成内容')) {
                showToast("暂无可复制的内容", true);
                return;
            }

            try {
                const blob = new Blob([content.innerHTML], { type: 'text/html' });
                const textBlob = new Blob([content.innerText], { type: 'text/plain' });
                const item = new ClipboardItem({
                    'text/html': blob,
                    'text/plain': textBlob
                });
                navigator.clipboard.write([item]).then(() => {
                    showToast("📋 微信富文本已复制！可以直接在手机微信粘贴。");
                }).catch(() => {
                    navigator.clipboard.writeText(content.innerText);
                    showToast("已复制纯文本格式内容");
                });
            } catch (e) {
                showToast("复制失败，请长按文本复制", true);
            }
        }

        async function triggerMobilePublish() {
            const previewContent = document.getElementById('mobilePreviewContent');
            if (!previewContent || previewContent.innerText.includes('暂无生成内容')) {
                showToast("⚠️ 请先在【选题与生成】中点击生成文章，再推送到草稿箱！", true);
                switchView('edit');
                return;
            }

            const btn = document.getElementById('mobilePublishBtn');
            const spinner = document.getElementById('mobilePubSpinner');
            const text = document.getElementById('mobilePubText');

            btn.disabled = true;
            spinner.style.display = "inline-block";
            text.innerText = "正在推送到微信公众号草稿箱...";

            try {
                const resp = await fetch("/api/publish", { method: "POST" });
                const data = await resp.json();
                if (data.code === 200) {
                    showToast("🚀 成功推送到微信草稿箱！手机已收到推送提醒。");
                } else {
                    showToast("推送草稿箱失败: " + data.message, true);
                }
            } catch (err) {
                showToast("网络通信异常: " + err, true);
            } finally {
                btn.disabled = false;
                spinner.style.display = "none";
                text.innerText = "📤 一键推送到微信公众号草稿箱";
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            fetchHotTopics('all');
        });
    </script>
</body>
</html>
"""

class MobilePublisherHandler(SimpleHTTPRequestHandler):
    """自媒体 H5 控制台请求处理器"""

    def _send_json(self, data: dict, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        if path == "/api/crawl":
            query = parse_qs(parsed.query)
            cat = query.get("category", ["all"])[0]
            try:
                topics = DefenseCrawler.fetch_multi_source_topics(category=cat, limit=20)
                self._send_json({"code": 200, "topics": topics})
            except Exception as e:
                logger.error(f"抓取热点异常: {e}")
                self._send_json({"code": 500, "message": str(e)})
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/generate":
            self._handle_generate()
            return

        if path == "/api/publish":
            self._handle_publish()
            return

        self.send_error(404, "Not Found")

    def _handle_generate(self):
        """处理文章生成请求"""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )

            topic = form.getvalue("topic", "").strip()
            raw_content = ""

            if "file" in form and form["file"].filename:
                file_item = form["file"]
                upload_dir = BASE_DIR / "scratch" / "uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                saved_path = upload_dir / file_item.filename

                with open(saved_path, "wb") as f:
                    f.write(file_item.file.read())

                logger.info(f"接收到用户上传文件: {saved_path}")
                if saved_path.suffix.lower() == ".pdf":
                    raw_content = ContentParser.extract_from_pdf(str(saved_path))
                else:
                    raw_content = ContentParser.extract_from_text_file(str(saved_path))

            if not raw_content and topic:
                raw_content = f"焦点话题研判指引：{topic}"

            if not raw_content:
                self._send_json({"code": 400, "message": "未接收到有效的报告内容或研判话题"})
                return

            # 1. 深度 AI 写作
            writer = AIWriter()
            article_data = writer.generate_article(raw_content=raw_content, user_focus=topic)

            title = article_data.get("title", "全球防务观察")
            digest = article_data.get("digest", "观察全球防务与地缘博弈。")
            md_content = article_data.get("markdown_content", "")

            # 2. 生成配图 (快手可图)
            img_path = ImageService.generate_topic_image(
                topic=title,
                article_summary=digest
            )
            cover_path = CoverGenerator.crop_to_wechat_ratio(img_path)

            # 3. 排版
            html_content = WeChatFormatter.format_to_wechat_html(
                markdown_text=md_content,
                author=settings.WECHAT_AUTHOR
            )

            # 统计字数
            clean_text = "".join(md_content.split())
            word_count = len(clean_text)
            read_time = max(1, round(word_count / 380))

            # 缓存
            CURRENT_CACHE["title"] = title
            CURRENT_CACHE["digest"] = digest
            CURRENT_CACHE["html_content"] = html_content
            CURRENT_CACHE["markdown_content"] = md_content
            CURRENT_CACHE["cover_image"] = cover_path
            CURRENT_CACHE["word_count"] = word_count
            CURRENT_CACHE["read_time"] = read_time

            self._send_json({
                "code": 200,
                "title": title,
                "digest": digest,
                "html_content": html_content,
                "word_count": word_count,
                "read_time": read_time,
                "cover_image": cover_path
            })

        except Exception as e:
            logger.error(f"处理生成请求失败: {e}", exc_info=True)
            self._send_json({"code": 500, "message": str(e)})

    def _handle_publish(self):
        """推送草稿箱"""
        try:
            if not CURRENT_CACHE["title"] or not CURRENT_CACHE["html_content"]:
                self._send_json({"code": 400, "message": "暂无待发布内容，请先执行生成！"})
                return

            wechat_client = WeChatClient()

            # 1. 上传封面
            logger.info("正在上传封面永久素材至微信 CDN...")
            thumb_media_id = wechat_client.upload_permanent_material(
                file_path=CURRENT_CACHE["cover_image"],
                material_type="image"
            )

            # 2. 上传图文草稿
            logger.info("正在推送至微信草稿箱...")
            article = {
                "title": CURRENT_CACHE["title"],
                "author": settings.WECHAT_AUTHOR,
                "digest": CURRENT_CACHE["digest"],
                "content": CURRENT_CACHE["html_content"],
                "thumb_media_id": thumb_media_id,
                "show_cover_pic": 1
            }

            media_id = wechat_client.add_draft(articles=[article])

            # 3. 记录已处理
            DefenseCrawler.save_history(CURRENT_CACHE["title"])

            # 4. 触发通知
            Notifier.send_all(
                title=f"【局势洞见】草稿推送成功: 《{CURRENT_CACHE['title']}》",
                content=(
                    f"文章标题：《{CURRENT_CACHE['title']}》\n"
                    f"文章字数：{CURRENT_CACHE.get('word_count', 0)} 字\n"
                    f"草稿 Media ID：{media_id}\n\n"
                    f"请在手机「订阅号助手」App 中审核后一键群发！"
                )
            )

            self._send_json({
                "code": 200,
                "message": "成功推送到微信公众平台草稿箱",
                "media_id": media_id
            })

        except Exception as e:
            logger.error(f"推送草稿箱失败: {e}", exc_info=True)
            self._send_json({"code": 500, "message": str(e)})


def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, MobilePublisherHandler)
    logger.info("==================================================")
    logger.info("🛡️ 局势洞见 移动端智库级发布工作台已就绪！")
    logger.info(f"👉 访问地址: http://localhost:{PORT}")
    logger.info(f"👉 云服务器公网访问: http://<云服务器公网IP>:{PORT}")
    logger.info("==================================================")
    httpd.serve_forever()


if __name__ == '__main__':
    run()
