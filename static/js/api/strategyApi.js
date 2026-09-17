import { request } from './client.js';

export const strategyApi = {
    // 获取当前生效的智库策略与对话历史
    getCurrentStrategy() {
        return request('/api/strategy/current');
    },

    // 与 AI 策略总监对话，智能调优抓取雷达与研报偏好
    chatTune(message) {
        return request('/api/strategy/chat', {
            method: 'POST',
            body: JSON.stringify({ message })
        });
    },

    // 一键重置为系统默认智库策略
    resetStrategy() {
        return request('/api/strategy/reset', { method: 'POST' });
    },

    // 基于近期战报线索，AI 自动刷新今日雷达词
    refreshRadar(sampleTitles = []) {
        return request('/api/strategy/radar_refresh', {
            method: 'POST',
            body: JSON.stringify({ titles: sampleTitles })
        });
    },

    // 手动增删/管理雷达关键词
    updateKeywords(action, keyword = '', keywords = null) {
        return request('/api/strategy/keywords', {
            method: 'POST',
            body: JSON.stringify({ action, keyword, keywords })
        });
    }
};
