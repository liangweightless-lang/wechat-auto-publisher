import { request } from './client.js';

export const historyApi = {
    // 获取 SQLite 历史研报列表
    getHistory(limit = 20) {
        return request(`/api/articles/history?limit=${limit}`);
    },

    // 获取特定历史文章详情并装入内存
    getArticleById(id) {
        return request(`/api/articles/get?id=${id}`);
    }
};
