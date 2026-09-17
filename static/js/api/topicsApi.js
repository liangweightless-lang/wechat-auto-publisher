import { request } from './client.js';

export const topicsApi = {
    // 拉取聚类情报流 (带缓存穿透参数)
    fetchTopics(category = 'all', clustered = true, forceRefresh = false) {
        const refreshParam = forceRefresh ? '&refresh=1' : '';
        return request(`/api/topics?category=${category}&clustered=${clustered ? 1 : 0}${refreshParam}`);
    },
    
    // 扩展特定事件的官方权威公告与外交部答问
    expandOfficialSources(keyword, clusterName) {
        return request('/api/topics/expand_sources', {
            method: 'POST',
            body: JSON.stringify({ keyword, cluster_name: clusterName })
        });
    },

    // 实时爬取单篇正文深度研判
    fetchContent(url) {
        return request('/api/topics/fetch_content', {
            method: 'POST',
            body: JSON.stringify({ url })
        });
    }
};
