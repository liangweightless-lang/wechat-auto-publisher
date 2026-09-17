// 统一 HTTP 客户端封装
export async function request(url, options = {}) {
    try {
        const resp = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            },
            ...options
        });
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
        }
        return await resp.json();
    } catch (e) {
        console.error(`Request Error (${url}):`, e);
        throw e;
    }
}
