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
        refreshIcons();
    }
}

export function openBottomSheet(sheetId) {
    const mask = document.getElementById('sheetMask');
    const sheet = document.getElementById(sheetId);
    if (mask && sheet) {
        mask.classList.add('active');
        sheet.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

export function closeBottomSheet(sheetId) {
    const mask = document.getElementById('sheetMask');
    const sheet = document.getElementById(sheetId);
    if (mask && sheet) {
        mask.classList.remove('active');
        sheet.classList.remove('active');
        document.body.style.overflow = '';
    }
}

export function closeAllSheets() {
    const mask = document.getElementById('sheetMask');
    if (mask) mask.classList.remove('active');
    document.querySelectorAll('.bottom-sheet').forEach(s => s.classList.remove('active'));
    document.body.style.overflow = '';
}
