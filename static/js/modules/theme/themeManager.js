import { state } from '../../store/state.js';
import { refreshIcons } from '../../utils/dom.js';

export function initTheme() {
    const saved = localStorage.getItem('app_theme') || 'light';
    setTheme(saved);
}

export function toggleTheme() {
    const next = state.currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(next);
}

export function setTheme(theme) {
    state.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app_theme', theme);

    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
        btn.innerHTML = theme === 'dark'
            ? '<i data-lucide="sun" style="width: 17px; height: 17px;"></i>'
            : '<i data-lucide="moon" style="width: 17px; height: 17px;"></i>';
    }
    const icon = document.getElementById('themeLucideIcon');
    if (icon) {
        icon.setAttribute('data-lucide', theme === 'dark' ? 'sun' : 'moon');
    }
    refreshIcons();
}

export function openBottomSheet(sheetId) {
    const sheet = document.getElementById(sheetId);
    const backdrop = document.getElementById(sheetId + 'Backdrop');
    if (sheet) sheet.classList.add('active');
    if (backdrop) backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';

    if (sheetId === 'historySheet' && window.app && window.app.loadHistoryArticles) {
        window.app.loadHistoryArticles();
    }
    refreshIcons();
}

export function closeBottomSheet(sheetId) {
    const sheet = document.getElementById(sheetId);
    const backdrop = document.getElementById(sheetId + 'Backdrop');
    if (sheet) sheet.classList.remove('active');
    if (backdrop) backdrop.classList.remove('active');
    document.body.style.overflow = '';
}

export function closeAllSheets() {
    document.querySelectorAll('.mobile-bottom-sheet').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.sheet-backdrop').forEach(b => b.classList.remove('active'));
    document.body.style.overflow = '';
}
