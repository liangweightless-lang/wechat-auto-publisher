// 现代化 Toast 轻提示工具
let toastTimeout = null;

export function showToast(msg, type = 'info') {
    let toast = document.getElementById('appToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'appToast';
        toast.className = 'app-toast';
        document.body.appendChild(toast);
    }

    toast.className = `app-toast toast-${type} show`;
    toast.textContent = msg;

    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
    }, 2800);
}
