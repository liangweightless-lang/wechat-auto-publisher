// 全局状态管理单例 (Enterprise Reactive State Store)
export const state = {
    currentCategory: 'all',
    currentActivePlatform: 'wechat',
    currentTheme: 'light',
    
    // 选中的情报文章映射表 (Key: `${clusterId}_${idx}` -> Value: articleItem)
    selectedArticlesMap: new Map(),
    
    // 当前分类下的聚类数据
    currentClustersData: [],
    allClustersData: [],
    
    // 前端极速秒开缓存 (Key: category -> Value: clusters)
    clientClustersCache: new Map(),
    
    // 深度生成与流式长文状态
    currentGeneratedData: null,
    currentTopicData: null,
    selectedFile: null,
    isThinkingCollapsed: false,
    totalTimerInterval: null,
    startTime: 0,
    
    // AI 策略总监调优配置
    currentStrategy: null
};

// 状态变更辅助方法
export function clearSelectedArticles() {
    state.selectedArticlesMap.clear();
}

export function setSelectedArticle(key, item) {
    state.selectedArticlesMap.set(key, item);
}

export function removeSelectedArticle(key) {
    state.selectedArticlesMap.delete(key);
}

export function getSelectedArticlesList() {
    return Array.from(state.selectedArticlesMap.values());
}
