// 格式化与文本清洗辅助工具
export function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

export function formatRelativeTime(dateStr) {
    if (!dateStr) return '今日最新';
    return dateStr;
}
