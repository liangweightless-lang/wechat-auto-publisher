import { request } from './client.js';

export const publishApi = {
    // 微信公众号草稿箱一键发布
    publishToWechat() {
        return request('/api/publish', { method: 'POST' });
    },

    // 智库排版换肤与重新排版
    formatPreview(theme = 'think_tank') {
        return request('/api/format/preview', {
            method: 'POST',
            body: JSON.stringify({ theme })
        });
    },

    // 获取所有可用主题与视觉风格
    getThemes() {
        return request('/api/themes');
    }
};
