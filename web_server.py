HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>局势洞见 · 全球防务与智库发布系统</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #06080e;
            --bg-card: rgba(16, 23, 40, 0.75);
            --bg-card-hover: rgba(23, 33, 56, 0.85);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(56, 189, 248, 0.3);
            --primary-gradient: linear-gradient(135deg, #2563eb, #38bdf8);
            --wechat-gradient: linear-gradient(135deg, #059669, #10b981);
            --danger-gradient: linear-gradient(135deg, #dc2626, #f43f5e);
            --accent-blue: #38bdf8;
            --accent-coral: #fb7185;
            --accent-amber: #fbbf24;
            --accent-emerald: #34d399;
            --text-title: #f8fafc;
            --text-body: #94a3b8;
            --text-dim: #64748b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background-color: var(--bg-deep);
            color: var(--text-title);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding-bottom: calc(95px + env(safe-area-inset-bottom));
            background-image: 
                radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.15) 0%, transparent 65%),
                radial-gradient(circle at 100% 20%, rgba(56, 189, 248, 0.08) 0%, transparent 40%);
            background-attachment: fixed;
            overflow-x: hidden;
        }

        /* 顶部毛玻璃光晕导航 */
        .app-header {
            position: sticky;
            top: 0;
            z-index: 60;
            background: rgba(6, 8, 14, 0.82);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-glass);
            padding: 14px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .app-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .brand-icon-box {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 16px rgba(37, 99, 235, 0.35);
            font-size: 19px;
        }
        .brand-title {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 16.5px;
            font-weight: 700;
            letter-spacing: 0.2px;
            background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-sub {
            font-size: 10.5px;
            color: var(--text-dim);
            letter-spacing: 0.4px;
        }
        .system-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 500;
            color: var(--accent-emerald);
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.22);
            padding: 4px 10px;
            border-radius: 20px;
        }
        .pulse-dot {
            width: 6px;
            height: 6px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-emerald);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(52, 211, 153, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
        }

        /* 仿 iOS 18 悬浮双 Tab 导航 */
        .segmented-wrapper {
            padding: 12px 16px 4px 16px;
            max-width: 720px;
            margin: 0 auto;
            width: 100%;
        }
        .segmented-bar {
            background: rgba(16, 23, 40, 0.6);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            padding: 4px;
            display: flex;
            position: relative;
        }
        .tab-item {
            flex: 1;
            padding: 10px 0;
            text-align: center;
            font-size: 13.5px;
            font-weight: 600;
            color: var(--text-body);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            user-select: none;
        }
        .tab-item.active {
            background: rgba(30, 41, 59, 0.9);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }
        .tab-badge {
            width: 6px;
            height: 6px;
            background: var(--accent-blue);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-blue);
            display: none;
        }

        /* 主视图容器 */
        .content-view { display: none; padding: 12px 16px; max-width: 720px; margin: 0 auto; width: 100%; }
        .content-view.active { display: block; }

        /* 玻璃拟态卡片 */
        .glass-card {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            transition: transform 0.2s, border-color 0.2s;
        }
        .card-title-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }
        .card-label {
            font-size: 11.5px;
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .card-action-link {
            font-size: 11.5px;
            color: var(--text-dim);
            cursor: pointer;
            transition: color 0.2s;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .card-action-link:hover { color: var(--accent-blue); }

        /* 极简上传面板 */
        .upload-zone {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.3) 0%, rgba(15, 23, 42, 0.5) 100%);
            border: 1.5px dashed rgba(56, 189, 248, 0.35);
            border-radius: 14px;
            padding: 20px 16px;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        .upload-zone:active {
            background: rgba(56, 189, 248, 0.08);
            border-color: var(--accent-blue);
            transform: scale(0.99);
        }
        .upload-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }
        .upload-title {
            font-size: 13.5px;
            font-weight: 600;
            color: #f1f5f9;
        }
        .upload-desc {
            font-size: 11px;
            color: var(--text-dim);
        }

        /* 战区横向平滑滑动胶囊 */
        .chips-container {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 10px;
            margin-bottom: 14px;
            scrollbar-width: none;
            -webkit-overflow-scrolling: touch;
        }
        .chips-container::-webkit-scrollbar { display: none; }
        .zone-chip {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-glass);
            color: var(--text-body);
            padding: 7px 15px;
            border-radius: 24px;
            font-size: 12px;
            font-weight: 500;
            white-space: nowrap;
            flex-shrink: 0;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .zone-chip:active { transform: scale(0.96); }
        .zone-chip.active {
            background: linear-gradient(135deg, #1e40af, #2563eb);
            color: #ffffff;
            border-color: rgba(96, 165, 250, 0.6);
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
            font-weight: 600;
        }

        /* 热点卡片：信息层级深度优化 */
        .intel-card {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .intel-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3.5px;
            background: var(--accent-blue);
            opacity: 0.6;
            transition: width 0.2s;
        }
        .intel-card.official::before { background: var(--accent-coral); }
        .intel-card.tech::before { background: var(--accent-emerald); }
        .intel-card.power::before { background: var(--accent-amber); }
        .intel-card:active {
            background: rgba(30, 41, 59, 0.7);
            border-color: var(--accent-blue);
            transform: scale(0.985);
        }
        .intel-card:active::before { width: 5px; opacity: 1; }

        .intel-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .intel-tag {
            font-size: 10.5px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(56, 189, 248, 0.12);
            color: var(--accent-blue);
            border: 1px solid rgba(56, 189, 248, 0.2);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .intel-card.official .intel-tag {
            background: rgba(244, 63, 94, 0.12);
            color: var(--accent-coral);
            border-color: rgba(244, 63, 94, 0.25);
        }
        .intel-card.tech .intel-tag {
            background: rgba(52, 211, 153, 0.12);
            color: var(--accent-emerald);
            border-color: rgba(52, 211, 153, 0.25);
        }
        .intel-source {
            font-size: 11px;
            color: var(--text-dim);
        }
        .intel-title {
            font-size: 14.5px;
            font-weight: 600;
            color: #f1f5f9;
            line-height: 1.48;
            margin-bottom: 6px;
            letter-spacing: 0.1px;
        }
        .intel-desc {
            font-size: 12px;
            color: var(--text-body);
            line-height: 1.55;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        /* 焦点多行输入框 */
        .input-group {
            margin-top: 16px;
            border-top: 1px solid var(--border-glass);
            padding-top: 14px;
        }
        .input-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .input-label {
            font-size: 12.5px;
            font-weight: 600;
            color: #cbd5e1;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .btn-clear {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-glass);
            color: var(--text-dim);
            font-size: 11px;
            padding: 3px 9px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-clear:active { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }

        .luxury-textarea {
            width: 100%;
            background: rgba(6, 8, 14, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 12px 14px;
            color: #ffffff;
            font-size: 14px;
            line-height: 1.6;
            resize: none;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
            min-height: 80px;
        }
        .luxury-textarea:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
        }
        .luxury-textarea::placeholder { color: #475569; }

        /* 核心生成主按钮（高端渐变流光质感） */
        .btn-main-generate {
            width: 100%;
            background: linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #38bdf8 100%);
            background-size: 200% 200%;
            animation: gradientShift 6s ease infinite;
            color: #ffffff;
            border: none;
            padding: 16px;
            border-radius: 16px;
            font-size: 15.5px;
            font-weight: 700;
            letter-spacing: 0.3px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .btn-main-generate:active {
            transform: scale(0.98);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* 预览视图控制条 */
        .preview-dock {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .dock-meta {
            font-size: 12.5px;
            color: var(--text-dim);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .dock-meta strong { color: var(--accent-blue); font-weight: 600; }
        .btn-copy {
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.25);
            color: #93c5fd;
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        .btn-copy:active { background: rgba(56, 189, 248, 0.25); transform: scale(0.96); }

        /* 微信推文真实排版纸张容器 */
        .wechat-sheet {
            background: #ffffff;
            border-radius: 16px;
            padding: 20px 16px;
            min-height: 600px;
            color: #2d3748;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        }

        /* 底部常驻悬浮吸底大条（Floating Island Bar） */
        .floating-action-island {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 80;
            padding: 12px 18px calc(12px + env(safe-area-inset-bottom)) 18px;
            background: linear-gradient(180deg, rgba(6, 8, 14, 0) 0%, rgba(6, 8, 14, 0.95) 25%, rgba(6, 8, 14, 0.98) 100%);
            display: flex;
            justify-content: center;
        }
        .island-inner {
            max-width: 680px;
            width: 100%;
        }
        .btn-publish-glow {
            width: 100%;
            background: var(--wechat-gradient);
            color: #ffffff;
            border: none;
            padding: 16px;
            border-radius: 16px;
            font-size: 15.5px;
            font-weight: 700;
            letter-spacing: 0.3px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            box-shadow: 0 8px 24px rgba(16, 185, 129, 0.35);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .btn-publish-glow:active { transform: scale(0.98); }

        /* 旋转微指示器 */
        .spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255, 255, 255, 0.25);
            border-top-color: #ffffff;
            border-radius: 50%;
            animation: spin 0.75s linear infinite;
            display: none;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* 弹窗指示层 */
        .modal-mask {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(4, 6, 11, 0.88);
            backdrop-filter: blur(16px);
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
        .stepper-card {
            background: rgba(16, 23, 40, 0.95);
            border: 1px solid var(--border-glass);
            border-radius: 22px;
            width: 100%;
            max-width: 400px;
            padding: 26px 22px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
        }
        .stepper-header {
            text-align: center;
            margin-bottom: 20px;
        }
        .stepper-title {
            font-size: 17px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }
        .stepper-sub {
            font-size: 12px;
            color: var(--text-dim);
        }
        .step-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            font-size: 13.5px;
            color: var(--text-dim);
            transition: all 0.3s;
        }
        .step-row.active {
            color: var(--accent-blue);
            font-weight: 600;
            transform: translateX(4px);
        }
        .step-row.done {
            color: var(--accent-emerald);
        }
        .step-badge {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            border: 1.5px solid currentColor;
            flex-shrink: 0;
        }

        /* 悬浮 Toast 气泡 */
        #toast {
            position: fixed;
            top: 24px;
            left: 50%;
            transform: translateX(-50%);
            padding: 11px 22px;
            background: rgba(16, 23, 40, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            color: #ffffff;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 500;
            z-index: 999;
            display: none;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            white-space: nowrap;
        }
    </style>
</head>
<body>

    <!-- 顶部状态栏 -->
    <header class="app-header">
        <div class="app-brand">
            <div class="brand-icon-box">🛡️</div>
            <div>
                <div class="brand-title">局势洞见</div>
                <div class="brand-sub">DEFENSE INTELLIGENCE PLATFORM</div>
            </div>
        </div>
        <div class="system-pill">
            <div class="pulse-dot"></div>
            <span>智库引擎就绪</span>
        </div>
    </header>

    <!-- 悬浮分段控制器 -->
    <div class="segmented-wrapper">
        <div class="segmented-bar">
            <div class="tab-item active" id="tabNavEdit" onclick="switchView('edit')">
                <span>🎯 智库选题与生成</span>
            </div>
            <div class="tab-item" id="tabNavPreview" onclick="switchView('preview')">
                <span>📖 微信推文排版预览</span>
                <div class="tab-badge" id="previewDot"></div>
            </div>
        </div>
    </div>

    <!-- 1. 选题与生成视图 -->
    <div class="content-view active" id="viewEdit">

        <!-- 报告导入卡片 -->
        <div class="glass-card">
            <div class="card-title-row">
                <div class="card-label">📁 原始材料 / 智库研报导入</div>
                <div class="card-action-link" style="color: var(--text-dim);">支持 PDF / TXT</div>
            </div>
            <input type="file" id="mobileFileInput" accept=".pdf,.txt" style="display: none;" onchange="handleMobileFile(this)">
            <div class="upload-zone" onclick="document.getElementById('mobileFileInput').click()">
                <div class="upload-icon">📑</div>
                <div class="upload-title" id="mobileFileLabel">点击导入 PDF 智库报告或舆情原文</div>
                <div class="upload-desc">自动解析战役图表、交火时序与核心参数</div>
            </div>
        </div>

        <!-- 多源情报矩阵 -->
        <div class="glass-card">
            <div class="card-title-row">
                <div class="card-label">🌐 全球防务与官方公告矩阵</div>
                <div class="card-action-link" onclick="fetchHotTopics(activeCategory)">
                    <span>🔄 刷新前线态势</span>
                </div>
            </div>

            <!-- 滑动战区标签 -->
            <div class="chips-container">
                <div class="zone-chip active" onclick="selectCategory('all', this)">🌐 全域战略</div>
                <div class="zone-chip" onclick="selectCategory('official', this)">🏛️ 官方公告战报</div>
                <div class="zone-chip" onclick="selectCategory('middle_east', this)">🔴 红海中东</div>
                <div class="zone-chip" onclick="selectCategory('eurasia', this)">🔵 俄乌欧亚</div>
                <div class="zone-chip" onclick="selectCategory('tech', this)">🟢 硬核战法</div>
                <div class="zone-chip" onclick="selectCategory('power', this)">🟡 大国海权</div>
                <div class="zone-chip" onclick="selectCategory('rolling', this)">⚡ 实时快报</div>
            </div>

            <!-- 动态热点卡片列表 -->
            <div id="mobileHotList">
                <div style="color: var(--accent-blue); text-align: center; padding: 24px; font-size: 13px;">
                    正在探测多源防务与官方战报流...
                </div>
            </div>

            <!-- 自定义焦点输入 -->
            <div class="input-group">
                <div class="input-header">
                    <div class="input-label">✍️ 研判焦点话题：</div>
                    <button type="button" class="btn-clear" onclick="clearTopicInput()">✕ 清空</button>
                </div>
                <textarea class="luxury-textarea" id="mobileTopicInput" rows="3" 
                    oninput="autoResizeTextarea(this)" 
                    placeholder="从上方情报池点选，或直接输入焦点事件（例如：胡塞武装袭击沙特红海基地与爱国者损耗）..."></textarea>
                <div id="charCount" style="text-align: right; font-size: 11px; color: var(--text-dim); margin-top: 4px;">0 字</div>
            </div>
        </div>

        <!-- 启动深度生成大按钮 -->
        <button class="btn-main-generate" id="mobileGenBtn" onclick="triggerMobileGenerate()">
            <div class="spinner" id="mobileGenSpinner"></div>
            <span id="mobileGenText">🚀 开始深度研判并生成配图</span>
        </button>
    </div>

    <!-- 2. 微信排版仿真预览视图 -->
    <div class="content-view" id="viewPreview">
        <div class="preview-dock">
            <div class="dock-meta">
                <span>正文状态:</span>
                <strong id="statWordCount">待生成</strong>
                <span>|</span>
                <span id="statReadTime">推文预览</span>
            </div>
            <button class="btn-copy" onclick="copyWechatHtml()">
                <span>📋 一键复制微信富文本</span>
            </button>
        </div>

        <!-- 微信正文内容容器 -->
        <div class="wechat-sheet" id="mobilePreviewContent">
            <div style="text-align: center; padding: 80px 20px; color: #94a3b8;">
                <div style="font-size: 48px; margin-bottom: 14px;">📰</div>
                <div style="font-weight: 600; font-size: 16px; color: #334155;">暂无生成内容</div>
                <div style="font-size: 13px; color: #64748b; margin-top: 8px;">请在「智库选题与生成」中选择素材后点击开始研判</div>
            </div>
        </div>
    </div>

    <!-- 悬浮吸底岛 (Floating Island Bar) -->
    <div class="floating-action-island">
        <div class="island-inner">
            <button class="btn-publish-glow" id="mobilePublishBtn" onclick="triggerMobilePublish()">
                <div class="spinner" id="mobilePubSpinner"></div>
                <span id="mobilePubText">📤 一键推送到微信公众平台草稿箱</span>
            </button>
        </div>
    </div>

    <!-- 多步骤进度弹层 (Progress Stepper) -->
    <div class="modal-mask" id="progressModal">
        <div class="stepper-card">
            <div class="stepper-header">
                <div class="stepper-title">智库研判引擎运转中</div>
                <div class="stepper-sub">多源交叉比对与因果链条建模</div>
            </div>

            <div class="step-row" id="step1">
                <div class="step-badge">1</div>
                <div>官方战报交叉比对与前置风控</div>
            </div>
            <div class="step-row" id="step2">
                <div class="step-badge">2</div>
                <div>还原事件前世今生与冲突因果链</div>
            </div>
            <div class="step-row" id="step3">
                <div class="step-badge">3</div>
                <div>决战兵器谱与幕后国家技术溯源</div>
            </div>
            <div class="step-row" id="step4">
                <div class="step-badge">4</div>
                <div>快手可图生成 2.35:1 电影级战地大片</div>
            </div>
            <div class="step-row" id="step5">
                <div class="step-badge">5</div>
                <div>微信专属 Inline CSS 引擎排版装配</div>
            </div>
        </div>
    </div>

    <!-- 悬浮 Toast 提示 -->
    <div id="toast"></div>

    <script>
        let mobileSelectedFile = null;
        let activeCategory = 'all';

        function showToast(msg, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.border = isError ? "1px solid rgba(244, 63, 94, 0.4)" : "1px solid rgba(52, 211, 153, 0.4)";
            t.style.display = "block";
            setTimeout(() => { t.style.display = "none"; }, 3200);
        }

        function switchView(viewName) {
            document.querySelectorAll('.content-view').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-item').forEach(el => el.classList.remove('active'));

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
                document.getElementById('mobileFileLabel').style.color = "var(--accent-blue)";
                showToast("已成功选定报告文件！");
            }
        }

        function selectCategory(cat, el) {
            activeCategory = cat;
            document.querySelectorAll('.zone-chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            fetchHotTopics(cat);
        }

        async function fetchHotTopics(cat = 'all') {
            const list = document.getElementById('mobileHotList');
            list.innerHTML = '<div style="color: var(--accent-blue); text-align: center; padding: 24px; font-size: 13px;">正在探测最新战区情报...</div>';
            try {
                const resp = await fetch(`/api/crawl?category=${cat}`);
                const data = await resp.json();
                if (data.code === 200 && data.topics.length) {
                    list.innerHTML = '';
                    data.topics.forEach(t => {
                        const item = document.createElement('div');
                        let catClass = t.category === 'official' ? 'official' : (t.category === 'tech' ? 'tech' : (t.category === 'power' ? 'power' : ''));
                        item.className = `intel-card ${catClass}`;
                        item.onclick = () => {
                            const inp = document.getElementById('mobileTopicInput');
                            inp.value = t.title;
                            autoResizeTextarea(inp);
                            showToast("已填入焦点话题！");
                            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                        };
                        item.innerHTML = `
                            <div class="intel-meta">
                                <span class="intel-tag">${t.level || t.keyword || '战区态势'}</span>
                                <span class="intel-source">${t.source || '公开防务通报'}</span>
                            </div>
                            <div class="intel-title">${t.title}</div>
                            <div class="intel-desc">${t.summary || ''}</div>
                        `;
                        list.appendChild(item);
                    });
                } else {
                    list.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 24px; font-size: 12px;">暂无该分类动态，可直接输入研究话题</div>';
                }
            } catch (e) {
                list.innerHTML = '<div style="color: var(--accent-coral); padding: 16px; font-size: 12px;">拉取异常: ' + e + '</div>';
            }
        }

        function updateStep(stepNum) {
            for (let i = 1; i <= 5; i++) {
                const el = document.getElementById('step' + i);
                el.classList.remove('active', 'done');
                if (i < stepNum) {
                    el.classList.add('done');
                    el.querySelector('.step-badge').innerText = '✓';
                } else if (i === stepNum) {
                    el.classList.add('active');
                    el.querySelector('.step-badge').innerText = i;
                } else {
                    el.querySelector('.step-badge').innerText = i;
                }
            }
        }

        function autoResizeTextarea(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.max(80, Math.min(textarea.scrollHeight, 220)) + 'px';
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
                showToast("⚠️ 请先点选上方话题或选择 PDF 报告！", true);
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
                    document.getElementById('previewDot').style.display = 'block';

                    const words = data.word_count || Math.round(data.html_content.length / 2);
                    document.getElementById('statWordCount').innerText = `${words.toLocaleString()} 字`;
                    document.getElementById('statReadTime').innerText = `预计阅读 ${Math.ceil(words / 400)} 分钟`;

                    showToast("🎉 智库级深度推文已生成就绪！");
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
                    showToast("📋 微信富文本已复制！可直接在手机微信粘贴。");
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
            text.innerText = "正在推送到微信公众平台草稿箱...";

            try {
                const resp = await fetch("/api/publish", { method: "POST" });
                const data = await resp.json();
                if (data.code === 200) {
                    showToast("🚀 成功推送到草稿箱！手机已收到推送提醒。");
                } else {
                    showToast("推送草稿箱失败: " + data.message, true);
                }
            } catch (err) {
                showToast("网络通信异常: " + err, true);
            } finally {
                btn.disabled = false;
                spinner.style.display = "none";
                text.innerText = "📤 一键推送到微信公众平台草稿箱";
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
