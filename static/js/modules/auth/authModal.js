// 现代化高颜值登录鉴权与会话拦截系统 (Linear/Vercel Aesthetic & Zero-Config Auth)
import { refreshIcons } from '../../utils/dom.js';
import { showToast } from '../../utils/toast.js';

let isAuthInitialized = false;

/**
 * 拦截全局 window.fetch，为所有 /api 请求自动注入 Authorization: Bearer
 * 并集中捕获 401 未登录异常
 */
function setupFetchInterceptor() {
    const originalFetch = window.fetch;
    window.fetch = async function(url, options = {}) {
        options = options || {};
        options.headers = options.headers || {};

        const token = localStorage.getItem('auth_token');
        if (token && typeof url === 'string' && url.includes('/api/')) {
            if (options.headers instanceof Headers) {
                if (!options.headers.has('Authorization')) {
                    options.headers.set('Authorization', `Bearer ${token}`);
                }
            } else if (typeof options.headers === 'object') {
                if (!options.headers['Authorization']) {
                    options.headers['Authorization'] = `Bearer ${token}`;
                }
            }
        }

        try {
            const response = await originalFetch(url, options);
            if (response.status === 401 && typeof url === 'string' && !url.includes('/api/auth/login') && !url.includes('/api/auth/check')) {
                console.warn('[Auth]: 捕获到 401 未授权请求，唤起登录窗口');
                localStorage.removeItem('auth_token');
                showLoginModal();
            }
            return response;
        } catch (err) {
            throw err;
        }
    };
}

/**
 * 初始化鉴权体系
 */
export async function initAuth() {
    if (isAuthInitialized) return;
    isAuthInitialized = true;

    setupFetchInterceptor();
    renderAuthDom();
    renderUserNavCapsule();

    // 检查本地 Token
    const token = localStorage.getItem('auth_token');
    if (!token) {
        showLoginModal();
        return;
    }

    try {
        const resp = await fetch('/api/auth/check');
        const res = await resp.json();
        if (res.code === 200) {
            hideLoginModal();
            updateUserNav(res.user?.username || 'admin');
        } else {
            showLoginModal();
        }
    } catch (e) {
        showLoginModal();
    }
}

/**
 * 动态渲染全屏登录 DOM 结构
 */
function renderAuthDom() {
    if (document.getElementById('authOverlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'authOverlay';
    overlay.className = 'auth-overlay';
    overlay.innerHTML = `
        <div class="auth-card" id="authCard">
            <div class="auth-brand-header">
                <div class="auth-logo-badge">
                    <i data-lucide="shield-alert" style="width: 28px; height: 28px;"></i>
                </div>
                <h1 class="auth-brand-title">
                    局势洞见
                    <span class="auth-brand-badge">防务创作中枢</span>
                </h1>
                <p class="auth-brand-subtitle">国家安全与地缘战报智能创作工作台</p>
            </div>

            <div class="auth-error-banner" id="authErrorBanner">
                <i data-lucide="alert-circle" style="width: 15px; height: 15px; flex-shrink: 0;"></i>
                <span id="authErrorText">账号或密码错误</span>
            </div>

            <form id="authLoginForm" onsubmit="window.app.handleLoginSubmit(event)">
                <div class="auth-form-group">
                    <label class="auth-label">管理员账号</label>
                    <div class="auth-input-wrapper">
                        <i data-lucide="user" class="auth-input-icon"></i>
                        <input type="text" id="authUsername" class="auth-input" value="admin" placeholder="输入管理员账号" autocomplete="username" required>
                    </div>
                </div>

                <div class="auth-form-group">
                    <label class="auth-label">访问口令</label>
                    <div class="auth-input-wrapper">
                        <i data-lucide="lock" class="auth-input-icon"></i>
                        <input type="password" id="authPassword" class="auth-input" placeholder="输入访问密钥 / 口令" autocomplete="current-password" required>
                        <button type="button" class="auth-toggle-pwd" onclick="window.app.toggleAuthPwdVisibility()">
                            <i data-lucide="eye" id="authPwdEyeIcon" style="width: 17px; height: 17px;"></i>
                        </button>
                    </div>
                </div>

                <button type="submit" class="auth-submit-btn" id="authSubmitBtn">
                    <span id="authSubmitText">立即安全进入</span>
                    <i data-lucide="arrow-right" id="authSubmitIcon" style="width: 16px; height: 16px;"></i>
                </button>
            </form>

            <div class="auth-footer-hint">
                <span>初始默认口令为 <code>admin888</code>，登录后可随时更改</span>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    refreshIcons();
}

/**
 * 在顶部 Header 右侧挂载用户身份胶囊
 */
function renderUserNavCapsule() {
    const actionsNav = document.querySelector('.navbar-actions');
    if (!actionsNav || document.getElementById('userNavCapsule')) return;

    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    wrapper.innerHTML = `
        <div class="user-nav-capsule" id="userNavCapsule" onclick="window.app.toggleUserDropdownMenu(event)">
            <span class="user-online-dot"></span>
            <span id="navUsernameText">admin</span>
            <i data-lucide="chevron-down" style="width: 12px; height: 12px; opacity: 0.6;"></i>
        </div>
        <div class="user-dropdown-menu" id="userDropdownMenu">
            <button class="user-dropdown-item" onclick="window.app.openChangePwdModal()">
                <i data-lucide="key-round" style="width: 14px; height: 14px;"></i>
                <span>修改访问密码</span>
            </button>
            <div style="height: 1px; background: var(--border); margin: 4px 0;"></div>
            <button class="user-dropdown-item danger" onclick="window.app.triggerLogout()">
                <i data-lucide="log-out" style="width: 14px; height: 14px;"></i>
                <span>退出登录</span>
            </button>
        </div>
    `;

    actionsNav.appendChild(wrapper);
    refreshIcons();

    // 点击外部自动收起下拉菜单
    document.addEventListener('click', (e) => {
        const menu = document.getElementById('userDropdownMenu');
        const capsule = document.getElementById('userNavCapsule');
        if (menu && !menu.contains(e.target) && capsule && !capsule.contains(e.target)) {
            menu.classList.remove('show');
        }
    });
}

function updateUserNav(username) {
    const el = document.getElementById('navUsernameText');
    if (el) el.innerText = username;
}

export function showLoginModal() {
    const overlay = document.getElementById('authOverlay');
    if (overlay) {
        overlay.classList.remove('auth-hidden');
        const pwdInput = document.getElementById('authPassword');
        if (pwdInput) {
            pwdInput.value = '';
            setTimeout(() => pwdInput.focus(), 150);
        }
    }
}

export function hideLoginModal() {
    const overlay = document.getElementById('authOverlay');
    if (overlay) {
        overlay.classList.add('auth-hidden');
    }
}

/**
 * 切换密码可见性
 */
export function toggleAuthPwdVisibility() {
    const pwdInput = document.getElementById('authPassword');
    const eyeIcon = document.getElementById('authPwdEyeIcon');
    if (!pwdInput) return;

    if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
        if (eyeIcon) eyeIcon.setAttribute('data-lucide', 'eye-off');
    } else {
        pwdInput.type = 'password';
        if (eyeIcon) eyeIcon.setAttribute('data-lucide', 'eye');
    }
    refreshIcons();
}

/**
 * 处理登录提交
 */
export async function handleLoginSubmit(e) {
    if (e) e.preventDefault();

    const username = document.getElementById('authUsername')?.value.trim();
    const password = document.getElementById('authPassword')?.value;
    const btn = document.getElementById('authSubmitBtn');
    const btnText = document.getElementById('authSubmitText');
    const errBanner = document.getElementById('authErrorBanner');
    const errText = document.getElementById('authErrorText');
    const card = document.getElementById('authCard');

    if (!username || !password) {
        showAuthError('请输入账号与访问口令');
        return;
    }

    if (btn) btn.disabled = true;
    if (btnText) btnText.innerText = '身份校验中...';
    if (errBanner) errBanner.classList.remove('show');

    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const res = await resp.json();

        if (res.code === 200 && res.token) {
            localStorage.setItem('auth_token', res.token);
            updateUserNav(res.user?.username || 'admin');
            hideLoginModal();
            showToast('身份核验通过，欢迎使用！', 'success');

            // 重新刷新选题数据
            if (window.app && window.app.refreshCurrentFeed) {
                window.app.refreshCurrentFeed();
            }
        } else {
            showAuthError(res.message || '账号或密码错误');
            if (card) {
                card.classList.remove('auth-shake');
                void card.offsetWidth; // 触发 reflow 重置动画
                card.classList.add('auth-shake');
            }
        }
    } catch (err) {
        showAuthError('网络请求失败: ' + err.message);
    } finally {
        if (btn) btn.disabled = false;
        if (btnText) btnText.innerText = '立即安全进入';
        refreshIcons();
    }
}

function showAuthError(msg) {
    const banner = document.getElementById('authErrorBanner');
    const text = document.getElementById('authErrorText');
    if (banner && text) {
        text.innerText = msg;
        banner.classList.add('show');
        refreshIcons();
    }
}

/**
 * 切换用户菜单展开/折叠
 */
export function toggleUserDropdownMenu(e) {
    if (e) e.stopPropagation();
    const menu = document.getElementById('userDropdownMenu');
    if (menu) menu.classList.toggle('show');
}

/**
 * 登出
 */
export async function triggerLogout() {
    const token = localStorage.getItem('auth_token');
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (_) {}

    localStorage.removeItem('auth_token');
    const menu = document.getElementById('userDropdownMenu');
    if (menu) menu.classList.remove('show');
    showLoginModal();
    showToast('已安全退出当前会话', 'info');
}

/**
 * 修改密码模态框
 */
export function openChangePwdModal() {
    const menu = document.getElementById('userDropdownMenu');
    if (menu) menu.classList.remove('show');

    const oldPwd = prompt('请输入当前旧密码:');
    if (oldPwd === null) return;
    if (!oldPwd) {
        showToast('旧密码不能为空', 'warning');
        return;
    }

    const newPwd = prompt('请输入新的访问口令 (长度至少4位):');
    if (newPwd === null) return;
    if (!newPwd || newPwd.trim().length < 4) {
        showToast('新密码长度不能少于 4 位', 'warning');
        return;
    }

    fetch('/api/auth/change_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_password: oldPwd, new_password: newPwd.trim() })
    }).then(r => r.json()).then(res => {
        if (res.code === 200) {
            showToast('密码修改成功，请使用新密码重新登录', 'success');
            localStorage.removeItem('auth_token');
            showLoginModal();
        } else {
            showToast(res.message || '修改密码失败', 'error');
        }
    }).catch(e => {
        showToast('网络请求异常: ' + e.message, 'error');
    });
}
