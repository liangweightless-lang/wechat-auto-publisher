import { request } from './client.js';

export const publishApi = {
    // 微信公众号草稿箱一键发布
    publishToWechat() {
        return request('/api/publish', { method: 'POST' });
    },

    // 智库排版换肤与重新排版 (传递当前文章 markdown 与 title 确保换肤格式绝对完整)
    formatPreview(theme = 'think_tank', markdown = '', title = '') {
        const payload = { theme };
        if (markdown) payload.markdown = markdown;
        if (title) payload.title = title;
        return request('/api/format/preview', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    // 获取所有可用主题与视觉风格
    getThemes() {
        return request('/api/themes');
    }
};
