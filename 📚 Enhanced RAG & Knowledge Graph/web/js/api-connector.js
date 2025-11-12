/**
 * AI-STACK V5.6 统一API连接器
 * 所有界面使用此库连接后端API
 */

class APIConnector {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async call(endpoint, options = {}) {
        const url = this.baseURL + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return { success: true, data };
            
        } catch (error) {
            console.error('API调用失败:', error);
            return { success: false, error: error.message };
        }
    }

    async get(endpoint) {
        return await this.call(endpoint, { method: 'GET' });
    }

    async post(endpoint, body) {
        return await this.call(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    async put(endpoint, body) {
        return await this.call(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    }

    async delete(endpoint) {
        return await this.call(endpoint, { method: 'DELETE' });
    }

    // 文件上传专用
    async uploadFile(endpoint, file, additionalData = {}) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            for (const [key, value] of Object.entries(additionalData)) {
                formData.append(key, value);
            }

            const response = await fetch(this.baseURL + endpoint, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return { success: true, data };
            
        } catch (error) {
            console.error('文件上传失败:', error);
            return { success: false, error: error.message };
        }
    }
}

// 创建全局实例
window.api = new APIConnector();

console.log('✅ API连接器已加载 - V5.6');


