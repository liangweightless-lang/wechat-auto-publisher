# -*- coding: utf-8 -*-
"""
微信公众号自动化发布系统 - 移动端专属可视化 Web 控制台 (Mobile-First)
对标市面主流 AI 智库与自媒体创作工作台交互规范：
1. 极简手机端设计：沉浸式状态栏、两段式分段导航、滑动战区标签；
2. 多源高密度防务情报矩阵：五大战区 50+ 智库选题池与实时滚动军情；
3. 过程透明度：多步骤思考与拆解进度指示器 (Progress Stepper)；
4. 深度推文微信仿真阅读：字数与阅读时长统计、一键复制微信富文本；
5. 吸底大按钮：一键推送到微信公众平台草稿箱，并触发 PushPlus 手机卡片通知。
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
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>局势洞见 · 防务智库发布工作台</title>
    <style>
        :root {
            --bg-base: #090d16;
            --bg-surface: #131b2e;
            --bg-card: #1c2742;
            --border-color: #2a3b5c;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --accent-red: #ef4444;
            --accent-gold: #f59e0b;
            --wechat-green: #07c160;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding-bottom: calc(85px + env(safe-area-inset-bottom));
        }

        /* 顶部沉浸式导航栏 */
        .app-header {
            position: sticky;
            top: 0;
            z-index: 50;
            background: rgba(9, 13, 22, 0.94);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .app-brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-icon {
            width: 34px;
            height: 34px;
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            border-radius: 9px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
        }
        .brand-title {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #ffffff;
        }
        .engine-status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11.5px;
            color: #4ade80;
            background: rgba(74, 222, 128, 0.1);
            padding: 4px 9px;
            border-radius: 12px;
            border: 1px solid rgba(74, 222, 128, 0.2);
        }
        .status-dot {
            width: 6px;
            height: 6px;
            background-color: #4ade80;
            border-radius: 50%;
            box-shadow: 0 0 8px #4ade80;
        }

        /* 主流分段控制器导航 */
        .segmented-nav {
            margin: 12px 16px 4px 16px;
            background: var(--bg-surface);
            padding: 4px;
            border-radius: 12px;
            display: flex;
            border: 1px solid var(--border-color);
        }
        .tab-btn {
            flex: 1;
            padding: 10px 0;
            text-align: center;
            font-size: 13.5px;
            font-weight: 600;
            color: var(--text-muted);
            border-radius: 9px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        .tab-btn.active {
            background: #1e293b;
            color: #ffffff;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.08);
        }
        .badge-dot {
            width: 7px;
            height: 7px;
            background: #10b981;
            border-radius: 50%;
            display: none;
        }

        /* 视图容器 */
        .view-section { display: none; padding: 12px 16px; max-width: 720px; margin: 0 auto; width: 100%; }
        .view-section.active { display: block; }

        /* 卡片容器 */
        .card {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 14px;
        }
        .card-header {
            font-size: 14.5px;
            font-weight: 700;
            color: #93c5fd;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* 战区滑动标签 */
        .pill-scroll {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 12px;
            scrollbar-width: none;
            -webkit-overflow-scrolling: touch;
        }
        .pill-scroll::-webkit-scrollbar { display: none; }
        .cat-chip {
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 7px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            white-space: nowrap;
            flex-shrink: 0;
            cursor: pointer;
            transition: all 0.2s;
        }
        .cat-chip.active {
            background: #2563eb;
            color: #ffffff;
            border-color: #3b82f6;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
        }

        /* 热点卡片瀑布流 */
        .topic-item {
            background: var(--bg-card);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .topic-item:active {
            background: rgba(37, 99, 235, 0.15);
            border-color: #3b82f6;
            transform: scale(0.99);
        }
        .topic-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .topic-badge {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            background: rgba(239, 68, 68, 0.18);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .topic-source {
            color: #64748b;
            font-size: 11.5px;
        }
        .topic-title {
            font-size: 14px;
            font-weight: 600;
            color: #f1f5f9;
            line-height: 1.45;
            margin-bottom: 6px;
        }
        .topic-summary {
            font-size: 12px;
            color: #94a3b8;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        /* 手机端上传控件 */
        .upload-dropzone {
            background: rgba(37, 99, 235, 0.05);
            border: 1.5px dashed #3b82f6;
            border-radius: 14px;
            padding: 20px 16px;
            text-align: center;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .upload-dropzone:active { background: rgba(37, 99, 235, 0.12); }

        /* 输入框 */
        .topic-textarea {
            width: 100%;
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px 14px;
            color: #ffffff;
            font-size: 14px;
            line-height: 1.5;
            resize: vertical;
            outline: none;
            margin-top: 8px;
        }
        .topic-textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(37,99,235,0.25); }
        .quick-chip {
            background: rgba(37, 99, 235, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 6px;
            white-space: nowrap;
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.2s;
        }
        .quick-chip:active { background: #2563eb; color: #ffffff; }


        /* 撰写与配图主按钮 */
        .btn-generate {
            width: 100%;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff;
            border: none;
            padding: 15px;
            border-radius: 14px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }
        .btn-generate:active { transform: scale(0.98); }
        .btn-generate:disabled { background: #334155; opacity: 0.6; box-shadow: none; cursor: not-allowed; }

        /* 多步骤进度弹层 (Progress Stepper) */
        .modal-mask {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(12px);
            z-index: 200;
            align-items: center;
            justify-content: center;
            padding: 24px;
            pointer-events: none;
        }
        .modal-mask.active {
            display: flex !important;
            pointer-events: auto !important;
        }
        .modal-box {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            width: 100%;
            max-width: 420px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .stepper-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            text-align: left;
            font-size: 13.5px;
            color: #64748b;
        }
        .stepper-item.active { color: #60a5fa; font-weight: 600; }
        .stepper-item.done { color: #10b981; }
        .stepper-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            border: 1.5px solid currentColor;
            flex-shrink: 0;
        }

        /* 预览视图控制面板 */
        .preview-meta-bar {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }
        .btn-copy-html {
            background: rgba(255,255,255,0.08);
            border: 1px solid var(--border-color);
            color: #93c5fd;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .btn-copy-html:active { background: rgba(37,99,235,0.2); }

        /* 微信文章全宽预览页面 */
        .preview-container {
            background: #ffffff;
            border-radius: 14px;
            padding: 16px;
            min-height: 500px;
            color: #2d3748;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }

        /* 底部常驻吸底条 */
        .bottom-action-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(9, 13, 22, 0.96);
            backdrop-filter: blur(16px);
            border-top: 1px solid var(--border-color);
            padding: 10px 16px calc(10px + env(safe-area-inset-bottom)) 16px;
            display: flex;
            gap: 12px;
        }
        .btn-wechat-push {
            flex: 1;
            background: var(--wechat-green);
            color: #ffffff;
            border: none;
            padding: 15px;
            border-radius: 14px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 14px rgba(7, 193, 96, 0.3);
        }
        .btn-wechat-push:active { transform: scale(0.98); }
        .btn-wechat-push:disabled { background: #334155; opacity: 0.5; box-shadow: none; cursor: not-allowed; }

        /* 旋转指示器 */
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: #ffffff;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            display: none;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* 气泡提示 */
        #toast {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 10px 20px;
            background: rgba(16, 185, 129, 0.95);
            color: #fff;
            border-radius: 20px;
            font-size: 13.5px;
            font-weight: 500;
            z-index: 999;
            display: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body>

    <!-- 顶部状态栏 -->
    <header class="app-header">
        <div class="app-brand">
            <div class="brand-icon">🛡️</div>
            <div>
                <div class="brand-title">局势洞见</div>
                <div style="font-size: 10.5px; color: var(--text-muted);">智库级全自动发布系统</div>
            </div>
        </div>
        <div class="engine-status">
            <div class="status-dot"></div>
            <span>智库引擎就绪</span>
        </div>
    </header>

    <!-- 分段导航 -->
    <div class="segmented-nav">
        <div class="tab-btn active" id="tabNavEdit" onclick="switchView('edit')">
            <span>🎯 智库选题与生成</span>
        </div>
        <div class="tab-btn" id="tabNavPreview" onclick="switchView('preview')">
            <span>📖 微信推文排版预览</span>
            <div class="badge-dot" id="previewDot"></div>
        </div>
    </div>

    <!-- 1. 选题与生成视图 -->
    <div class="view-section active" id="viewEdit">

        <!-- 智库报告导入卡片 -->
        <div class="card">
            <div class="card-header">
                <span>📁 智库报告 / 原始资料导入</span>
                <span style="font-size: 11px; color: var(--text-muted);">支持 PDF / TXT</span>
            </div>
            <input type="file" id="mobileFileInput" accept=".pdf,.txt" style="display: none;" onchange="handleMobileFile(this)">
            <div class="upload-dropzone" onclick="document.getElementById('mobileFileInput').click()">
                <div style="font-size: 26px;">📑</div>
                <div style="font-size: 13.5px; font-weight: 600; color: #93c5fd;" id="mobileFileLabel">点击选择或导入 PDF 舆情报告</div>
                <div style="font-size: 11px; color: var(--text-muted);">自动解析图表与战役数据</div>
            </div>
        </div>

        <!-- 多源防务热点情报矩阵 -->
        <div class="card">
            <div class="card-header">
                <span>🌐 多源防务热点情报池</span>
                <span style="font-size: 11px; color: #60a5fa; cursor: pointer;" onclick="fetchHotTopics(activeCategory)">🔄 刷新探测</span>
            </div>

            <!-- 滑动分类标签 -->
            <div class="pill-scroll">
                <div class="cat-chip active" onclick="selectCategory('all', this)">🌐 全域战略</div>
                <div class="cat-chip" onclick="selectCategory('official', this)">🏛️ 官方公告战报</div>
                <div class="cat-chip" onclick="selectCategory('middle_east', this)">🔴 红海中东</div>
                <div class="cat-chip" onclick="selectCategory('eurasia', this)">🔵 俄乌欧亚</div>
                <div class="cat-chip" onclick="selectCategory('tech', this)">🟢 硬核战法</div>
                <div class="cat-chip" onclick="selectCategory('power', this)">🟡 大国海权</div>
                <div class="cat-chip" onclick="selectCategory('rolling', this)">⚡ 实时快报</div>
            </div>

            <!-- 动态热点列表 -->
            <div id="mobileHotList">
                <div style="color: #60a5fa; text-align: center; padding: 16px; font-size: 13px;">正在探测最新战区情报...</div>
            </div>

            <!-- 自定义研判焦点输入 (多行自适应与快捷指令) -->
            <div style="margin-top: 16px; border-top: 1px dashed var(--border-color); padding-top: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="font-size: 13.5px; font-weight: 700; color: #93c5fd; display: flex; align-items: center; gap: 6px;">
                        <span>✍️ 焦点话题与研判指引</span>
                        <span style="font-size: 11px; color: var(--text-muted); font-weight: normal;">(多行自适应展开)</span>
                    </div>
                    <button type="button" onclick="clearTopicInput()" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #fca5a5; font-size: 11px; padding: 3px 8px; border-radius: 6px; cursor: pointer;">
                        ✕ 一键清空
                    </button>
                </div>

                <!-- 快捷指令标签 -->
                <div style="display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 4px; scrollbar-width: none;">
                    <span class="quick-chip" onclick="appendInstruction('重点拆解攻防武器型号与拦截效费比')">+ 硬核武器对抗</span>
                    <span class="quick-chip" onclick="appendInstruction('重点分析苏伊士运河通行量与国际油价外溢影响')">+ 航运油价冲击</span>
                    <span class="quick-chip" onclick="appendInstruction('重点推演美军航母与多国护航联盟的现实困局')">+ 美军护航困境</span>
                    <span class="quick-chip" onclick="appendInstruction('梳理也门南北分立与沙特十年军事行动历史宿怨')">+ 战史百年宿怨</span>
                </div>

                <div style="position: relative;">
                    <textarea class="topic-textarea" id="mobileTopicInput" rows="3" 
                        oninput="autoResizeTextarea(this)" 
                        placeholder="可直接点选上方情报，或长篇输入您的研究方向与补充指引（支持多行输入与自动展开）..."></textarea>
                    <div id="charCount" style="text-align: right; font-size: 11px; color: #64748b; margin-top: 4px;">0 字</div>
                </div>
            </div>
        </div>

        <!-- 启动深度生成大按钮 -->
        <button class="btn-generate" id="mobileGenBtn" onclick="triggerMobileGenerate()">
            <div class="spinner" id="mobileGenSpinner"></div>
            <span id="mobileGenText">🚀 启动 1800 字官方战报深度研判并配图</span>
        </button>
    </div>

    <!-- 2. 微信排版仿真预览视图 -->
    <div class="view-section" id="viewPreview">
        <!-- 统计与快捷操作栏 -->
        <div class="preview-meta-bar">
            <div>
                <span style="color: #93c5fd; font-weight: 600;" id="statWordCount">1,850 字</span>
                <span style="color: #64748b; margin: 0 4px;">|</span>
                <span style="color: #94a3b8;" id="statReadTime">预计阅读 4.5 分钟</span>
            </div>
            <button class="btn-copy-html" onclick="copyWechatHtml()">
                <span>📋 一键复制微信富文本</span>
            </button>
        </div>

        <!-- 微信正文内容容器 -->
        <div class="preview-container" id="mobilePreviewContent">
            <div style="text-align: center; padding: 70px 20px; color: #94a3b8;">
                <div style="font-size: 44px; margin-bottom: 12px;">📰</div>
                <div style="font-weight: 600; font-size: 15px; color: #cbd5e1;">暂无生成内容</div>
                <div style="font-size: 12px; margin-top: 6px;">请在「智库选题与生成」中选择素材后点击生成</div>
            </div>
        </div>
    </div>

    <!-- 手机底部常驻操作栏 -->
    <div class="bottom-action-bar">
        <button class="btn-wechat-push" id="mobilePublishBtn" onclick="triggerMobilePublish()">
            <div class="spinner" id="mobilePubSpinner"></div>
            <span id="mobilePubText">📤 一键推送到微信公众平台草稿箱</span>
        </button>
    </div>

    <!-- 多步骤思考指示弹窗 (Progress Stepper Modal) -->
    <div class="modal-mask" id="progressModal">
        <div class="modal-box">
            <div style="font-size: 16px; font-weight: 700; color: #ffffff; margin-bottom: 6px;">智库研判引擎启动中</div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 18px;">正在多线程交叉验证公开防务情报与战术参数</div>

            <div class="stepper-item" id="step1">
                <div class="stepper-icon">1</div>
                <div>多源防务信源交叉比对与前置风控</div>
            </div>
            <div class="stepper-item" id="step2">
                <div class="stepper-icon">2</div>
                <div>武器攻防参数拆解与战役态势建模</div>
            </div>
            <div class="stepper-item" id="step3">
                <div class="stepper-icon">3</div>
                <div>地缘宿怨穿透与生成万字级核心架构</div>
            </div>
            <div class="stepper-item" id="step4">
                <div class="stepper-icon">4</div>
                <div>快手可图生成 2.35:1 战场写实大片</div>
            </div>
            <div class="stepper-item" id="step5">
                <div class="stepper-icon">5</div>
                <div>微信专属 Inline CSS 引擎排版装配</div>
            </div>
        </div>
    </div>

    <!-- 浮动通知提示 -->
    <div id="toast"></div>

    <script>
        let mobileSelectedFile = null;
        let activeCategory = 'all';

        function showToast(msg, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.background = isError ? "rgba(239, 68, 68, 0.95)" : "rgba(16, 185, 129, 0.95)";
            t.style.display = "block";
            setTimeout(() => { t.style.display = "none"; }, 3500);
        }

        function switchView(viewName) {
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

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
                document.getElementById('mobileFileLabel').innerText = "已选: " + mobileSelectedFile.name;
                document.getElementById('mobileFileLabel').style.color = "#60a5fa";
                showToast("已成功选定报告文件！");
            }
        }

        function selectCategory(cat, el) {
            activeCategory = cat;
            document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            fetchHotTopics(cat);
        }

        async function fetchHotTopics(cat = 'all') {
            const list = document.getElementById('mobileHotList');
            list.innerHTML = '<div style="color: #60a5fa; text-align: center; padding: 16px; font-size: 13px;">正在探测最新战区情报...</div>';
            try {
                const resp = await fetch(`/api/crawl?category=${cat}`);
                const data = await resp.json();
                if (data.code === 200 && data.topics.length) {
                    list.innerHTML = '';
                    data.topics.forEach(t => {
                        const item = document.createElement('div');
                        item.className = 'topic-item';
                        item.onclick = () => {
                            const inp = document.getElementById('mobileTopicInput'); inp.value = t.title; autoResizeTextarea(inp);
                            showToast("已填入焦点话题！");
                            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                        };
                        item.innerHTML = `
                            <div class="topic-meta">
                                <span class="topic-badge"># ${t.level || t.keyword || '焦点'}</span>
                                <span class="topic-source">${t.source || '防务智库'}</span>
                            </div>
                            <div class="topic-title">${t.title}</div>
                            <div class="topic-summary">${t.summary || ''}</div>
                        `;
                        list.appendChild(item);
                    });
                } else {
                    list.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 16px; font-size: 12px;">暂无该分类选题，可手动输入</div>';
                }
            } catch (e) {
                list.innerHTML = '<div style="color: #ef4444; padding: 14px; font-size: 12px;">网络拉取异常: ' + e + '</div>';
            }
        }

        function updateStep(stepNum) {
            for (let i = 1; i <= 5; i++) {
                const el = document.getElementById('step' + i);
                el.classList.remove('active', 'done');
                if (i < stepNum) {
                    el.classList.add('done');
                    el.querySelector('.stepper-icon').innerText = '✓';
                } else if (i === stepNum) {
                    el.classList.add('active');
                    el.querySelector('.stepper-icon').innerText = i;
                } else {
                    el.querySelector('.stepper-icon').innerText = i;
                }
            }
        }

        async function triggerMobileGenerate() {
            const topic = document.getElementById('mobileTopicInput').value.trim();
            if (!mobileSelectedFile && !topic) {
                showToast("⚠️ 请先点选上方话题或选择 PDF 报告！", true);
                const inputEl = document.getElementById('mobileTopicInput');
                if (inputEl) { inputEl.focus(); }
                return;
            }

            const modal = document.getElementById('progressModal');
            modal.classList.add('active');
            updateStep(1);

            // 动态模拟步进体验
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
                    document.getElementById('mobilePublishBtn').disabled = false;
                    document.getElementById('previewDot').style.display = 'inline';

                    // 更新字数与时间
                    const words = data.word_count || Math.round(data.html_content.length / 2);
                    document.getElementById('statWordCount').innerText = `${words.toLocaleString()} 字`;
                    document.getElementById('statReadTime').innerText = `预计阅读 ${Math.ceil(words / 400)} 分钟`;

                    showToast("🎉 智库级深度长文已装配就绪！");
                    setTimeout(() => { switchView('preview'); }, 500);
                } else {
                    showToast("生成失败: " + data.message, true);
                }
            } catch (err) {
                clearTimeout(timer1); clearTimeout(timer2); clearTimeout(timer3); clearTimeout(timer4);
                modal.classList.remove('active');
                showToast("网络连接异常: " + err, true);
            }
        }

        
        function autoResizeTextarea(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.max(76, Math.min(textarea.scrollHeight, 220)) + 'px';
            const len = textarea.value.trim().length;
            const countEl = document.getElementById('charCount');
            if (countEl) countEl.innerText = len + ' 字';
        }

        function clearTopicInput() {
            const input = document.getElementById('mobileTopicInput');
            input.value = '';
            autoResizeTextarea(input);
            showToast("已清空研判输入框");
        }

        function appendInstruction(text) {
            const input = document.getElementById('mobileTopicInput');
            if (input.value.trim()) {
                input.value += '\n【研判侧重】：' + text;
            } else {
                input.value = '【研判侧重】：' + text;
            }
            autoResizeTextarea(input);
            showToast("已追加专业研判要求！");
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
                    showToast("📋 微信富文本已复制到手机剪贴板！可以直接在微信中粘贴。");
                }).catch(() => {
                    // 降级使用纯文本复制
                    navigator.clipboard.writeText(content.innerText);
                    showToast("已复制纯文本格式内容");
                });
            } catch (e) {
                showToast("复制失败，请手动长按复制", true);
            }
        }

        async function triggerMobilePublish() {
            const btn = document.getElementById('mobilePublishBtn');
            const spinner = document.getElementById('mobilePubSpinner');
            const text = document.getElementById('mobilePubText');

            const previewContent = document.getElementById('mobilePreviewContent');
            if (!previewContent || previewContent.innerText.includes('暂无生成内容')) {
                showToast("⚠️ 请先在【选题与生成】中点击生成文章，再推送到草稿箱！", true);
                switchView('edit');
                return;
            }

            btn.disabled = true;
            spinner.style.display = "inline-block";
            text.innerText = "正在推送到微信公众平台草稿箱...";

            try {
                const resp = await fetch("/api/publish", { method: "POST" });
                const data = await resp.json();
                if (data.code === 200) {
                    showToast("🚀 成功推送到微信草稿箱！手机已收到推送提醒。");
                    alert("🎉 恭喜！文章已成功写入【微信公众平台草稿箱】！\n\n您可以直接在手机打开「订阅号助手」App 或微信公众平台后台一键群发！");
                } else {
                    showToast("推送失败: " + data.message, true);
                }
            } catch (err) {
                showToast("网络异常: " + err, true);
            } finally {
                btn.disabled = false;
                spinner.style.display = "none";
                text.innerText = "📤 一键推送到微信公众平台草稿箱";
            }
        }

        // 初始化加载热点
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
