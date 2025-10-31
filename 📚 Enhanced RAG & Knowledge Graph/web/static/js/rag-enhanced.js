/**
 * RAG Enhanced Module - 智能RAG增强模块
 * 功能：文档处理、向量检索、知识图谱集成、智能问答
 */

class RAGEnhanced {
    constructor(config = {}) {
        this.config = {
            apiBaseUrl: config.apiBaseUrl || '/api/rag',
            chunkSize: config.chunkSize || 1000,
            chunkOverlap: config.chunkOverlap || 200,
            maxResults: config.maxResults || 10,
            similarityThreshold: config.similarityThreshold || 0.7,
            ...config
        };

        this.state = {
            documents: [],
            searchResults: [],
            currentQuery: '',
            isLoading: false,
            selectedDocument: null,
            knowledgeGraph: null
        };

        this.init();
    }

    /**
     * 初始化RAG模块
     */
    init() {
        this.bindEvents();
        this.loadDocuments();
        this.setupFileUpload();
        this.initializeKnowledgeGraph();

        console.log('RAG Enhanced Module initialized');
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 搜索事件
        const searchInput = document.getElementById('rag-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.handleSearch();
            });
        }

        // 文件操作事件
        document.addEventListener('click', this.handleDocumentClick.bind(this));

        // 键盘快捷键
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));

        // 窗口事件
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    }

    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 设置文件上传
     */
    setupFileUpload() {
        const uploadArea = document.getElementById('rag-upload-area');
        const fileInput = document.getElementById('rag-file-input');

        if (!uploadArea || !fileInput) return;

        // 拖放事件
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            this.handleFileUpload(files);
        });

        // 点击上传
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });
    }

    /**
     * 处理文件上传
     */
    async handleFileUpload(files) {
        if (!files.length) return;

        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }

        try {
            this.setLoading(true);

            const response = await fetch(`${this.config.apiBaseUrl}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.state.documents = [...this.state.documents, ...result.documents];

            this.renderDocumentList();
            this.showNotification('文件上传成功', 'success');

        } catch (error) {
            console.error('File upload error:', error);
            this.showNotification('文件上传失败', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 处理搜索
     */
    async handleSearch() {
        const searchInput = document.getElementById('rag-search-input');
        if (!searchInput) return;

        const query = searchInput.value.trim();
        if (!query) {
            this.state.searchResults = [];
            this.renderSearchResults();
            return;
        }

        this.state.currentQuery = query;
        this.state.isLoading = true;

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    max_results: this.config.maxResults,
                    similarity_threshold: this.config.similarityThreshold
                })
            });

            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }

            const results = await response.json();
            this.state.searchResults = results.results || [];

            // 更新知识图谱
            if (results.knowledge_graph) {
                this.updateKnowledgeGraph(results.knowledge_graph);
            }

            this.renderSearchResults();

        } catch (error) {
            console.error('Search error:', error);
            this.showNotification('搜索失败', 'error');
        } finally {
            this.state.isLoading = false;
            this.setLoading(false);
        }
    }

    /**
     * 渲染文档列表
     */
    renderDocumentList() {
        const container = document.getElementById('rag-file-list');
        if (!container) return;

        if (this.state.documents.length === 0) {
            container.innerHTML = `
                <div class="rag-empty-state">
                    <div class="rag-empty-icon">📄</div>
                    <div class="rag-empty-text">暂无文档</div>
                    <div class="rag-empty-hint">上传文档开始使用RAG功能</div>
                </div>
            `;
            return;
        }

        container.innerHTML = this.state.documents.map(doc => `
            <div class="rag-file-item ${this.state.selectedDocument?.id === doc.id ? 'active' : ''}"
                 data-doc-id="${doc.id}">
                <div class="rag-file-icon">
                    ${this.getFileIcon(doc.type)}
                </div>
                <div class="rag-file-info">
                    <div class="rag-file-name">${this.escapeHtml(doc.name)}</div>
                    <div class="rag-file-meta">
                        <span>${this.formatFileSize(doc.size)}</span>
                        <span>${this.formatDate(doc.uploaded_at)}</span>
                    </div>
                </div>
                <div class="rag-file-actions">
                    <button class="rag-action-btn" onclick="rag.deleteDocument('${doc.id}')" title="删除">
                        🗑️
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * 渲染搜索结果
     */
    renderSearchResults() {
        const container = document.getElementById('rag-results-container');
        if (!container) return;

        if (this.state.isLoading) {
            container.innerHTML = `
                <div class="rag-loading">
                    <div class="rag-spinner"></div>
                    <div>正在搜索中...</div>
                </div>
            `;
            return;
        }

        if (this.state.searchResults.length === 0) {
            container.innerHTML = `
                <div class="rag-empty-state">
                    <div class="rag-empty-icon">🔍</div>
                    <div class="rag-empty-text">暂无搜索结果</div>
                    <div class="rag-empty-hint">尝试使用不同的关键词搜索</div>
                </div>
            `;
            return;
        }

        container.innerHTML = this.state.searchResults.map((result, index) => `
            <div class="rag-result-item" data-result-index="${index}">
                <div class="rag-result-header">
                    <div class="rag-result-source">
                        ${this.getFileIcon(result.document_type)}
                        <span>${this.escapeHtml(result.document_name)}</span>
                    </div>
                    <div class="rag-result-confidence ${this.getConfidenceClass(result.similarity)}">
                        ${Math.round(result.similarity * 100)}%
                    </div>
                </div>
                <div class="rag-result-content">
                    <div class="rag-result-chunk">
                        ${this.highlightText(result.content, this.state.currentQuery)}
                    </div>
                    ${result.entities && result.entities.length > 0 ? `
                        <div class="rag-result-entities">
                            ${result.entities.map(entity => `
                                <span class="rag-entity-tag">${this.escapeHtml(entity)}</span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                <div class="rag-result-footer">
                    <button class="rag-action-btn" onclick="rag.viewSource('${result.document_id}', ${result.chunk_index})">
                        查看原文
                    </button>
                    <button class="rag-action-btn" onclick="rag.addToKnowledgeGraph(${index})">
                        添加到知识图谱
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * 文本高亮
     */
    highlightText(text, query) {
        if (!query) return this.escapeHtml(text);

        const escapedQuery = this.escapeRegex(query);
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        return this.escapeHtml(text).replace(regex, '<mark>$1</mark>');
    }

    /**
     * 转义正则表达式特殊字符
     */
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * HTML转义
     */
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    /**
     * 获取置信度CSS类
     */
    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'rag-confidence-high';
        if (confidence >= 0.6) return 'rag-confidence-medium';
        return 'rag-confidence-low';
    }

    /**
     * 获取文件图标
     */
    getFileIcon(fileType) {
        const icons = {
            'pdf': '📕',
            'doc': '📘',
            'docx': '📘',
            'txt': '📄',
            'md': '📝',
            'image': '🖼️',
            'code': '💻',
            'default': '📁'
        };

        return icons[fileType] || icons.default;
    }

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 格式化日期
     */
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('zh-CN');
    }

    /**
     * 设置加载状态
     */
    setLoading(loading) {
        this.state.isLoading = loading;
        const loader = document.getElementById('rag-loading');
        if (loader) {
            loader.style.display = loading ? 'block' : 'none';
        }
    }

    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `rag-notification rag-notification-${type}`;
        notification.innerHTML = `
            <div class="rag-notification-content">
                <span class="rag-notification-message">${message}</span>
                <button class="rag-notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // 添加到页面
        const container = document.getElementById('rag-notifications') || this.createNotificationContainer();
        container.appendChild(notification);

        // 自动移除
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * 创建通知容器
     */
    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'rag-notifications';
        container.className = 'rag-notifications';
        document.body.appendChild(container);
        return container;
    }

    /**
     * 初始化知识图谱
     */
    initializeKnowledgeGraph() {
        // 这里会集成知识图谱可视化组件
        console.log('Knowledge graph integration initialized');
    }

    /**
     * 更新知识图谱
     */
    updateKnowledgeGraph(graphData) {
        this.state.knowledgeGraph = graphData;
        // 触发知识图谱更新事件
        this.triggerEvent('knowledgeGraphUpdate', graphData);
    }

    /**
     * 触发自定义事件
     */
    triggerEvent(eventName, data) {
        const event = new CustomEvent(`rag:${eventName}`, { detail: data });
        document.dispatchEvent(event);
    }

    /**
     * 处理文档点击
     */
    handleDocumentClick(event) {
        const fileItem = event.target.closest('.rag-file-item');
        if (fileItem) {
            const docId = fileItem.dataset.docId;
            this.selectDocument(docId);
        }
    }

    /**
     * 选择文档
     */
    selectDocument(docId) {
        const document = this.state.documents.find(doc => doc.id === docId);
        if (document) {
            this.state.selectedDocument = document;
            this.renderDocumentList();
            this.triggerEvent('documentSelected', document);
        }
    }

    /**
     * 删除文档
     */
    async deleteDocument(docId) {
        if (!confirm('确定要删除这个文档吗？')) return;

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/documents/${docId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Delete failed: ${response.statusText}`);
            }

            this.state.documents = this.state.documents.filter(doc => doc.id !== docId);
            if (this.state.selectedDocument?.id === docId) {
                this.state.selectedDocument = null;
            }

            this.renderDocumentList();
            this.showNotification('文档删除成功', 'success');

        } catch (error) {
            console.error('Delete error:', error);
            this.showNotification('文档删除失败', 'error');
        }
    }

    /**
     * 查看原文
     */
    async viewSource(documentId, chunkIndex) {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/documents/${documentId}/chunks/${chunkIndex}`);
            if (!response.ok) throw new Error('Failed to fetch source');

            const source = await response.json();
            this.showSourceModal(source);

        } catch (error) {
            console.error('View source error:', error);
            this.showNotification('获取原文失败', 'error');
        }
    }

    /**
     * 显示原文模态框
     */
    showSourceModal(source) {
        // 实现原文查看模态框
        console.log('Show source modal:', source);
    }

    /**
     * 添加到知识图谱
     */
    addToKnowledgeGraph(resultIndex) {
        const result = this.state.searchResults[resultIndex];
        if (result) {
            this.triggerEvent('addToKnowledgeGraph', result);
            this.showNotification('已添加到知识图谱', 'success');
        }
    }

    /**
     * 处理键盘快捷键
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K: 聚焦搜索框
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.getElementById('rag-search-input');
            if (searchInput) searchInput.focus();
        }

        // Escape: 清除搜索
        if (event.key === 'Escape') {
            const searchInput = document.getElementById('rag-search-input');
            if (searchInput) {
                searchInput.value = '';
                this.state.searchResults = [];
                this.renderSearchResults();
            }
        }
    }

    /**
     * 页面卸载前处理
     */
    handleBeforeUnload(event) {
        if (this.state.isLoading) {
            event.preventDefault();
            event.returnValue = '正在处理中，确定要离开吗？';
        }
    }

    /**
     * 加载文档列表
     */
    async loadDocuments() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/documents`);
            if (response.ok) {
                const data = await response.json();
                this.state.documents = data.documents || [];
                this.renderDocumentList();
            }
        } catch (error) {
            console.error('Load documents error:', error);
        }
    }

    /**
     * 获取模块状态
     */
    getState() {
        return { ...this.state };
    }

    /**
     * 更新配置
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }

    /**
     * 销毁实例
     */
    destroy() {
        // 清理事件监听器
        document.removeEventListener('click', this.handleDocumentClick);
        document.removeEventListener('keydown', this.handleKeyboardShortcuts);
        window.removeEventListener('beforeunload', this.handleBeforeUnload);

        console.log('RAG Enhanced Module destroyed');
    }
}

// 全局实例管理
window.RAGEnhanced = RAGEnhanced;

// 自动初始化
document.addEventListener('DOMContentLoaded', function() {
    if (window.ragConfig) {
        window.rag = new RAGEnhanced(window.ragConfig);
    } else {
        window.rag = new RAGEnhanced();
    }
});

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RAGEnhanced;
}