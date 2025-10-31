/**
 * AI Stack Super Enhanced - 实时智能搜索器
 * 文件: real-time-search.js
 * 路径: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/static/js/
 * 功能: 实时搜索、智能提示、结果高亮、搜索历史
 */

class RealTimeSearch {
    constructor(options = {}) {
        this.options = {
            searchUrl: options.searchUrl || '/api/rag/search',
            suggestUrl: options.suggestUrl || '/api/rag/suggest',
            debounceDelay: options.debounceDelay || 300,
            minQueryLength: options.minQueryLength || 2,
            maxSuggestions: options.maxSuggestions || 10,
            enableHistory: options.enableHistory !== false,
            maxHistoryItems: options.maxHistoryItems || 50,
            enableVoiceSearch: options.enableVoiceSearch !== false,
            highlightMatches: options.highlightMatches !== false,
            searchFields: options.searchFields || ['title', 'content', 'keywords'],
            ...options
        };

        this.searchInput = null;
        this.suggestionsContainer = null;
        this.resultsContainer = null;
        this.searchHistory = [];
        this.currentQuery = '';
        this.isListening = false;
        this.recognition = null;
        this.debounceTimer = null;
        this.isInitialized = false;

        this.initializeSearch();
    }

    initializeSearch() {
        this.loadSearchHistory();
        this.setupVoiceRecognition();
        this.isInitialized = true;
        console.log('RealTimeSearch: 初始化完成');
    }

    attachToInput(inputElement, suggestionsElement = null, resultsElement = null) {
        this.searchInput = inputElement;
        this.suggestionsContainer = suggestionsElement;
        this.resultsContainer = resultsElement;

        if (!this.searchInput) {
            console.error('RealTimeSearch: 搜索输入框未找到');
            return;
        }

        this.setupEventListeners();
        console.log('RealTimeSearch: 已附加到输入框', this.searchInput);
    }

    setupEventListeners() {
        // 输入事件
        this.searchInput.addEventListener('input', this.handleInput.bind(this));

        // 键盘事件
        this.searchInput.addEventListener('keydown', this.handleKeyDown.bind(this));

        // 焦点事件
        this.searchInput.addEventListener('focus', this.handleFocus.bind(this));
        this.searchInput.addEventListener('blur', this.handleBlur.bind(this));

        // 清除按钮事件
        this.setupClearButton();

        console.log('RealTimeSearch: 事件监听器设置完成');
    }

    setupClearButton() {
        // 添加清除按钮
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'search-clear-button';
        clearButton.innerHTML = '×';
        clearButton.style.cssText = `
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            color: #999;
            display: none;
        `;

        clearButton.addEventListener('click', () => {
            this.clearSearch();
        });

        this.searchInput.parentNode.style.position = 'relative';
        this.searchInput.parentNode.appendChild(clearButton);

        // 根据输入显示/隐藏清除按钮
        this.searchInput.addEventListener('input', () => {
            clearButton.style.display = this.searchInput.value ? 'block' : 'none';
        });
    }

    handleInput(event) {
        const query = event.target.value.trim();
        this.currentQuery = query;

        // 显示/隐藏清除按钮
        const clearButton = this.searchInput.parentNode.querySelector('.search-clear-button');
        if (clearButton) {
            clearButton.style.display = query ? 'block' : 'none';
        }

        // 防抖处理
        clearTimeout(this.debounceTimer);

        if (query.length === 0) {
            this.hideSuggestions();
            this.clearResults();
            return;
        }

        if (query.length < this.options.minQueryLength) {
            this.showMinLengthMessage();
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.performSearch(query);
        }, this.options.debounceDelay);

        // 实时显示搜索建议
        this.showSuggestions(query);
    }

    handleKeyDown(event) {
        switch (event.key) {
            case 'Enter':
                event.preventDefault();
                this.executeSearch(this.currentQuery);
                break;

            case 'ArrowDown':
                event.preventDefault();
                this.navigateSuggestions(1);
                break;

            case 'ArrowUp':
                event.preventDefault();
                this.navigateSuggestions(-1);
                break;

            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }

    handleFocus() {
        if (this.currentQuery && this.suggestionsContainer) {
            this.showSuggestions(this.currentQuery);
        }
    }

    handleBlur() {
        // 延迟隐藏以确保点击建议项能正常触发
        setTimeout(() => {
            this.hideSuggestions();
        }, 200);
    }

    async performSearch(query) {
        if (!query || query.length < this.options.minQueryLength) {
            return;
        }

        // 显示加载状态
        this.showLoading();

        try {
            const response = await fetch(this.options.searchUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    fields: this.options.searchFields,
                    limit: 20,
                    highlight: this.options.highlightMatches
                })
            });

            if (!response.ok) {
                throw new Error(`搜索请求失败: ${response.status}`);
            }

            const results = await response.json();
            this.displayResults(results);
            this.addToHistory(query);

            // 触发搜索完成事件
            this.emitSearchEvent('searchCompleted', { query, results });

        } catch (error) {
            console.error('RealTimeSearch: 搜索错误', error);
            this.showError('搜索失败: ' + error.message);

            // 触发搜索错误事件
            this.emitSearchEvent('searchError', { query, error });
        }
    }

    async showSuggestions(query) {
        if (!this.suggestionsContainer || query.length < this.options.minQueryLength) {
            this.hideSuggestions();
            return;
        }

        try {
            const suggestions = await this.fetchSuggestions(query);
            this.displaySuggestions(suggestions, query);
        } catch (error) {
            console.warn('RealTimeSearch: 获取建议失败', error);
            // 不显示错误，静默失败
        }
    }

    async fetchSuggestions(query) {
        const response = await fetch(this.options.suggestUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                limit: this.options.maxSuggestions
            })
        });

        if (!response.ok) {
            throw new Error(`建议请求失败: ${response.status}`);
        }

        return await response.json();
    }

    displaySuggestions(suggestions, query) {
        if (!this.suggestionsContainer) return;

        // 清空现有建议
        this.suggestionsContainer.innerHTML = '';

        if (!suggestions || suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }

        // 创建建议列表
        const suggestionsList = document.createElement('ul');
        suggestionsList.className = 'search-suggestions-list';
        suggestionsList.style.cssText = `
            list-style: none;
            margin: 0;
            padding: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-height: 300px;
            overflow-y: auto;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
        `;

        // 添加建议项
        suggestions.forEach((suggestion, index) => {
            const suggestionItem = document.createElement('li');
            suggestionItem.className = 'search-suggestion-item';
            suggestionItem.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
            `;

            // 高亮匹配文本
            const highlightedText = this.highlightText(suggestion.text, query);
            suggestionItem.innerHTML = highlightedText;

            // 鼠标事件
            suggestionItem.addEventListener('mouseenter', () => {
                suggestionItem.style.background = '#f5f5f5';
            });
            suggestionItem.addEventListener('mouseleave', () => {
                suggestionItem.style.background = '';
            });
            suggestionItem.addEventListener('click', () => {
                this.selectSuggestion(suggestion.text);
            });

            suggestionsList.appendChild(suggestionItem);
        });

        // 添加搜索历史（如果有）
        if (this.options.enableHistory && this.searchHistory.length > 0) {
            this.addHistoryToSuggestions(suggestionsList, query);
        }

        this.suggestionsContainer.appendChild(suggestionsList);
        this.suggestionsContainer.style.display = 'block';

        // 存储当前建议项引用
        this.currentSuggestions = Array.from(suggestionsList.querySelectorAll('.search-suggestion-item'));
        this.selectedSuggestionIndex = -1;
    }

    addHistoryToSuggestions(suggestionsList, query) {
        const historyHeader = document.createElement('li');
        historyHeader.className = 'search-suggestion-header';
        historyHeader.textContent = '搜索历史';
        historyHeader.style.cssText = `
            padding: 8px 12px;
            background: #f8f9fa;
            font-weight: bold;
            color: #666;
            border-bottom: 1px solid #e9ecef;
        `;
        suggestionsList.appendChild(historyHeader);

        const matchingHistory = this.searchHistory
            .filter(item => item.query.toLowerCase().includes(query.toLowerCase()))
            .slice(0, 5);

        matchingHistory.forEach(historyItem => {
            const historyElement = document.createElement('li');
            historyElement.className = 'search-suggestion-item history-item';
            historyElement.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            `;

            const querySpan = document.createElement('span');
            querySpan.textContent = historyItem.query;

            const timeSpan = document.createElement('span');
            timeSpan.textContent = this.formatTimeAgo(historyItem.timestamp);
            timeSpan.style.cssText = 'font-size: 12px; color: #999;';

            historyElement.appendChild(querySpan);
            historyElement.appendChild(timeSpan);

            historyElement.addEventListener('click', () => {
                this.selectSuggestion(historyItem.query);
            });

            suggestionsList.appendChild(historyElement);
        });
    }

    navigateSuggestions(direction) {
        if (!this.currentSuggestions || this.currentSuggestions.length === 0) {
            return;
        }

        // 移除之前选中的样式
        if (this.selectedSuggestionIndex >= 0) {
            this.currentSuggestions[this.selectedSuggestionIndex].style.background = '';
        }

        // 计算新的选中索引
        this.selectedSuggestionIndex += direction;

        if (this.selectedSuggestionIndex < 0) {
            this.selectedSuggestionIndex = this.currentSuggestions.length - 1;
        } else if (this.selectedSuggestionIndex >= this.currentSuggestions.length) {
            this.selectedSuggestionIndex = 0;
        }

        // 应用选中样式
        this.currentSuggestions[this.selectedSuggestionIndex].style.background = '#007bff';
        this.currentSuggestions[this.selectedSuggestionIndex].style.color = 'white';

        // 更新输入框内容
        const selectedText = this.currentSuggestions[this.selectedSuggestionIndex].textContent ||
                           this.currentSuggestions[this.selectedSuggestionIndex].query;
        this.searchInput.value = selectedText;
        this.currentQuery = selectedText;
    }

    selectSuggestion(suggestionText) {
        this.searchInput.value = suggestionText;
        this.currentQuery = suggestionText;
        this.hideSuggestions();
        this.executeSearch(suggestionText);
    }

    executeSearch(query) {
        this.hideSuggestions();
        this.performSearch(query);
    }

    displayResults(results) {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = '';

        if (!results || results.length === 0) {
            this.showNoResults();
            return;
        }

        const resultsList = document.createElement('div');
        resultsList.className = 'search-results-list';

        results.forEach((result, index) => {
            const resultElement = this.createResultElement(result, index);
            resultsList.appendChild(resultElement);
        });

        this.resultsContainer.appendChild(resultsList);

        // 显示结果统计
        this.showResultsStats(results.length);
    }

    createResultElement(result, index) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'search-result-item';
        resultDiv.style.cssText = `
            padding: 16px;
            border-bottom: 1px solid #eee;
            background: white;
            border-radius: 4px;
            margin-bottom: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        `;

        // 标题
        const title = document.createElement('h3');
        title.className = 'result-title';
        title.style.margin = '0 0 8px 0';

        if (result.url) {
            const titleLink = document.createElement('a');
            titleLink.href = result.url;
            titleLink.textContent = result.title || '无标题';
            titleLink.style.cssText = 'color: #007bff; text-decoration: none;';
            title.appendChild(titleLink);
        } else {
            title.textContent = result.title || '无标题';
        }

        // 内容摘要
        const content = document.createElement('div');
        content.className = 'result-content';
        content.style.cssText = 'color: #666; line-height: 1.5; margin-bottom: 8px;';

        if (result.highlight) {
            content.innerHTML = result.highlight;
        } else if (result.content) {
            const truncatedContent = result.content.length > 200 ?
                result.content.substring(0, 200) + '...' : result.content;
            content.textContent = truncatedContent;
        }

        // 元信息
        const meta = document.createElement('div');
        meta.className = 'result-meta';
        meta.style.cssText = 'font-size: 12px; color: #999;';

        if (result.score) {
            const score = document.createElement('span');
            score.textContent = `相关度: ${(result.score * 100).toFixed(1)}%`;
            meta.appendChild(score);
        }

        if (result.timestamp) {
            if (meta.children.length > 0) meta.appendChild(document.createTextNode(' | '));
            const time = document.createElement('span');
            time.textContent = this.formatTime(result.timestamp);
            meta.appendChild(time);
        }

        if (result.source) {
            if (meta.children.length > 0) meta.appendChild(document.createTextNode(' | '));
            const source = document.createElement('span');
            source.textContent = `来源: ${result.source}`;
            meta.appendChild(source);
        }

        resultDiv.appendChild(title);
        resultDiv.appendChild(content);
        resultDiv.appendChild(meta);

        return resultDiv;
    }

    showLoading() {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="search-loading" style="text-align: center; padding: 20px; color: #666;">
                <div style="margin-bottom: 10px;">🔍</div>
                <div>搜索中...</div>
            </div>
        `;
    }

    showNoResults() {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="search-no-results" style="text-align: center; padding: 40px; color: #666;">
                <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
                <h3 style="margin: 0 0 8px 0;">未找到相关结果</h3>
                <p>尝试使用其他关键词或调整搜索条件</p>
            </div>
        `;
    }

    showError(message) {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="search-error" style="text-align: center; padding: 20px; color: #d9534f;">
                <div style="margin-bottom: 10px;">❌</div>
                <div>${message}</div>
            </div>
        `;
    }

    showResultsStats(count) {
        // 可以在结果容器上方显示统计信息
        const statsElement = document.createElement('div');
        statsElement.className = 'search-stats';
        statsElement.style.cssText = `
            padding: 8px 0;
            color: #666;
            font-size: 14px;
            border-bottom: 1px solid #eee;
            margin-bottom: 16px;
        `;
        statsElement.textContent = `找到 ${count} 个结果`;

        this.resultsContainer.insertBefore(statsElement, this.resultsContainer.firstChild);
    }

    showMinLengthMessage() {
        if (!this.suggestionsContainer) return;

        this.suggestionsContainer.innerHTML = `
            <div class="search-min-length-message" style="padding: 8px 12px; color: #999; font-size: 14px;">
                请输入至少 ${this.options.minQueryLength} 个字符
            </div>
        `;
        this.suggestionsContainer.style.display = 'block';
    }

    hideSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.style.display = 'none';
            this.suggestionsContainer.innerHTML = '';
            this.currentSuggestions = null;
            this.selectedSuggestionIndex = -1;
        }
    }

    clearResults() {
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = '';
        }
    }

    clearSearch() {
        this.searchInput.value = '';
        this.currentQuery = '';
        this.hideSuggestions();
        this.clearResults();

        // 隐藏清除按钮
        const clearButton = this.searchInput.parentNode.querySelector('.search-clear-button');
        if (clearButton) {
            clearButton.style.display = 'none';
        }

        // 触发清除事件
        this.emitSearchEvent('searchCleared', {});
    }

    // 搜索历史管理
    addToHistory(query) {
        if (!this.options.enableHistory) return;

        // 移除重复项
        this.searchHistory = this.searchHistory.filter(item =>
            item.query.toLowerCase() !== query.toLowerCase()
        );

        // 添加到历史记录
        this.searchHistory.unshift({
            query: query,
            timestamp: Date.now()
        });

        // 限制历史记录数量
        if (this.searchHistory.length > this.options.maxHistoryItems) {
            this.searchHistory = this.searchHistory.slice(0, this.options.maxHistoryItems);
        }

        this.saveSearchHistory();
    }

    loadSearchHistory() {
        if (!this.options.enableHistory) return;

        try {
            const stored = localStorage.getItem('rag_search_history');
            if (stored) {
                this.searchHistory = JSON.parse(stored);
            }
        } catch (error) {
            console.warn('RealTimeSearch: 加载搜索历史失败', error);
            this.searchHistory = [];
        }
    }

    saveSearchHistory() {
        if (!this.options.enableHistory) return;

        try {
            localStorage.setItem('rag_search_history', JSON.stringify(this.searchHistory));
        } catch (error) {
            console.warn('RealTimeSearch: 保存搜索历史失败', error);
        }
    }

    clearSearchHistory() {
        this.searchHistory = [];
        try {
            localStorage.removeItem('rag_search_history');
        } catch (error) {
            console.warn('RealTimeSearch: 清除搜索历史失败', error);
        }

        this.emitSearchEvent('historyCleared', {});
    }

    getSearchHistory() {
        return [...this.searchHistory];
    }

    // 语音搜索
    setupVoiceRecognition() {
        if (!this.options.enableVoiceSearch) return;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();

            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'zh-CN';

            this.recognition.onstart = () => {
                this.isListening = true;
                this.emitSearchEvent('voiceStart', {});
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.searchInput.value = transcript;
                this.currentQuery = transcript;
                this.executeSearch(transcript);
            };

            this.recognition.onerror = (event) => {
                console.error('RealTimeSearch: 语音识别错误', event.error);
                this.emitSearchEvent('voiceError', { error: event.error });
            };

            this.recognition.onend = () => {
                this.isListening = false;
                this.emitSearchEvent('voiceEnd', {});
            };
        } else {
            console.warn('RealTimeSearch: 浏览器不支持语音识别');
        }
    }

    startVoiceSearch() {
        if (this.recognition && !this.isListening) {
            this.recognition.start();
        }
    }

    stopVoiceSearch() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    // 工具方法
    highlightText(text, query) {
        if (!this.options.highlightMatches || !query) {
            return this.escapeHtml(text);
        }

        const escapedQuery = this.escapeRegex(query);
        const regex = new RegExp(`(${escapedQuery})`, 'gi');

        return this.escapeHtml(text).replace(regex, '<mark style="background: #ffeb3b; padding: 2px 0;">$1</mark>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleString('zh-CN');
    }

    formatTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 7) return `${days}天前`;

        return new Date(timestamp).toLocaleDateString('zh-CN');
    }

    // 事件管理
    on(event, callback) {
        if (!this.eventListeners) {
            this.eventListeners = {};
        }
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    emitSearchEvent(event, data) {
        if (this.eventListeners && this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`RealTimeSearch: 事件 ${event} 处理错误`, error);
                }
            });
        }
    }

    // 公共方法
    setSearchUrl(url) {
        this.options.searchUrl = url;
    }

    setSuggestUrl(url) {
        this.options.suggestUrl = url;
    }

    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
    }

    destroy() {
        // 清理事件监听器
        if (this.searchInput) {
            this.searchInput.removeEventListener('input', this.handleInput);
            this.searchInput.removeEventListener('keydown', this.handleKeyDown);
            this.searchInput.removeEventListener('focus', this.handleFocus);
            this.searchInput.removeEventListener('blur', this.handleBlur);
        }

        // 停止语音识别
        this.stopVoiceSearch();

        // 清理定时器
        clearTimeout(this.debounceTimer);

        this.isInitialized = false;
        console.log('RealTimeSearch: 已销毁');
    }
}

// 全局访问
window.RealTimeSearch = RealTimeSearch;
console.log('real-time-search.js: 实时智能搜索器加载完成');