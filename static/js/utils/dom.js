// DOM 选择与辅助工具模块
export function $(selector) {
    return document.querySelector(selector);
}

export function $$(selector) {
    return Array.from(document.querySelectorAll(selector));
}

export function refreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }
}
