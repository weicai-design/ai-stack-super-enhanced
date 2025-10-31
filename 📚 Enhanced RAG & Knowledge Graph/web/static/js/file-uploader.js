/**
 * AI Stack Super Enhanced - 通用文件上传器
 * 文件: file-uploader.js
 * 路径: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/static/js/
 * 功能: 多格式文件上传、分块处理、进度跟踪、格式验证
 */

class UniversalFileUploader {
    constructor(options = {}) {
        this.options = {
            uploadUrl: options.uploadUrl || '/api/rag/upload',
            chunkSize: options.chunkSize || 5 * 1024 * 1024, // 5MB
            maxFileSize: options.maxFileSize || 500 * 1024 * 1024, // 500MB
            allowedTypes: options.allowedTypes || this.getAllSupportedTypes(),
            maxConcurrentUploads: options.maxConcurrentUploads || 3,
            enableChunking: options.enableChunking !== false,
            autoUpload: options.autoUpload !== false,
            ...options
        };

        this.uploadQueue = [];
        this.activeUploads = new Map();
        this.progressCallbacks = new Map();
        this.isInitialized = false;

        this.initializeUploader();
    }

    getAllSupportedTypes() {
        return {
            // 办公文档
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-powerpoint': ['.ppt'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
            'text/plain': ['.txt'],

            // 电子书
            'application/epub+zip': ['.epub'],
            'application/x-mobipocket-ebook': ['.mobi'],
            'application/vnd.amazon.ebook': ['.azw'],

            // 编程文件
            'text/x-python': ['.py'],
            'text/javascript': ['.js'],
            'text/x-java': ['.java'],
            'text/x-c++': ['.cpp', '.cc', '.cxx'],
            'text/x-c': ['.c'],
            'text/x-csharp': ['.cs'],
            'text/x-php': ['.php'],
            'text/x-ruby': ['.rb'],
            'text/x-go': ['.go'],
            'text/x-rust': ['.rs'],
            'text/html': ['.html', '.htm'],
            'text/css': ['.css'],
            'application/json': ['.json'],
            'application/xml': ['.xml'],

            // 图片文件
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
            'image/bmp': ['.bmp'],
            'image/svg+xml': ['.svg'],
            'image/tiff': ['.tiff', '.tif'],
            'image/webp': ['.webp'],

            // 音频文件
            'audio/mpeg': ['.mp3'],
            'audio/wav': ['.wav'],
            'audio/ogg': ['.ogg'],
            'audio/aac': ['.aac'],
            'audio/flac': ['.flac'],
            'audio/x-m4a': ['.m4a'],

            // 视频文件
            'video/mp4': ['.mp4'],
            'video/avi': ['.avi'],
            'video/mov': ['.mov'],
            'video/wmv': ['.wmv'],
            'video/flv': ['.flv'],
            'video/webm': ['.webm'],
            'video/quicktime': ['.qt'],

            // 思维导图
            'application/x-freemind': ['.mm'],
            'application/x-xmind': ['.xmind'],

            // 数据文件
            'text/csv': ['.csv'],
            'application/vnd.ms-access': ['.mdb', '.accdb'],
            'application/x-sql': ['.sql'],

            // 压缩文件
            'application/zip': ['.zip'],
            'application/x-rar-compressed': ['.rar'],
            'application/x-7z-compressed': ['.7z'],
            'application/x-tar': ['.tar'],
            'application/gzip': ['.gz']
        };
    }

    initializeUploader() {
        this.setupEventListeners();
        this.isInitialized = true;
        console.log('UniversalFileUploader: 初始化完成');
    }

    setupEventListeners() {
        // 全局拖放事件
        document.addEventListener('dragover', this.handleDragOver.bind(this));
        document.addEventListener('drop', this.handleDrop.bind(this));
        document.addEventListener('dragleave', this.handleDragLeave.bind(this));

        console.log('UniversalFileUploader: 事件监听器设置完成');
    }

    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        event.dataTransfer.dropEffect = 'copy';

        // 添加拖放区域高亮
        document.body.classList.add('file-drag-over');
    }

    handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();

        if (!event.relatedTarget || event.relatedTarget.nodeName === 'HTML') {
            document.body.classList.remove('file-drag-over');
        }
    }

    handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();

        document.body.classList.remove('file-drag-over');

        const files = Array.from(event.dataTransfer.files);
        this.processFiles(files);

        console.log('UniversalFileUploader: 拖放文件处理完成', files);
    }

    processFiles(files) {
        const validFiles = [];
        const invalidFiles = [];

        files.forEach(file => {
            if (this.validateFile(file)) {
                validFiles.push(file);
            } else {
                invalidFiles.push(file);
            }
        });

        // 处理有效文件
        validFiles.forEach(file => {
            this.addToUploadQueue(file);
        });

        // 处理无效文件
        if (invalidFiles.length > 0) {
            this.showInvalidFilesError(invalidFiles);
        }

        // 开始上传
        if (this.options.autoUpload) {
            this.processUploadQueue();
        }

        return {
            valid: validFiles,
            invalid: invalidFiles
        };
    }

    validateFile(file) {
        // 文件大小验证
        if (file.size > this.options.maxFileSize) {
            console.warn(`文件 ${file.name} 超过大小限制`);
            return false;
        }

        // 文件类型验证
        const isTypeSupported = this.isFileTypeSupported(file);
        if (!isTypeSupported) {
            console.warn(`文件 ${file.name} 类型不支持`);
            return false;
        }

        // 文件名称验证
        if (!this.validateFileName(file.name)) {
            console.warn(`文件 ${file.name} 名称无效`);
            return false;
        }

        return true;
    }

    isFileTypeSupported(file) {
        // 通过MIME类型检查
        if (this.options.allowedTypes[file.type]) {
            return true;
        }

        // 通过文件扩展名检查
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        for (const mimeType in this.options.allowedTypes) {
            if (this.options.allowedTypes[mimeType].includes(extension)) {
                return true;
            }
        }

        return false;
    }

    validateFileName(filename) {
        // 基础文件名验证
        const invalidChars = /[<>:"/\\|?*\x00-\x1F]/g;
        const reservedNames = /^(con|prn|aux|nul|com[0-9]|lpt[0-9])$/i;

        if (invalidChars.test(filename)) {
            return false;
        }

        if (reservedNames.test(filename.split('.')[0])) {
            return false;
        }

        return filename.length > 0 && filename.length <= 255;
    }

    addToUploadQueue(file) {
        const fileId = this.generateFileId(file);
        const queueItem = {
            id: fileId,
            file: file,
            status: 'queued',
            progress: 0,
            chunks: [],
            uploadedChunks: 0,
            totalChunks: 0,
            startTime: null,
            endTime: null
        };

        // 准备分块（如果启用）
        if (this.options.enableChunking && file.size > this.options.chunkSize) {
            this.prepareFileChunks(queueItem);
        }

        this.uploadQueue.push(queueItem);

        // 触发文件添加事件
        this.emitFileEvent('fileAdded', queueItem);

        console.log(`UniversalFileUploader: 文件 ${file.name} 添加到队列`, queueItem);

        return fileId;
    }

    generateFileId(file) {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        return `${timestamp}_${random}_${file.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
    }

    prepareFileChunks(queueItem) {
        const file = queueItem.file;
        const chunkSize = this.options.chunkSize;
        const totalChunks = Math.ceil(file.size / chunkSize);

        queueItem.totalChunks = totalChunks;
        queueItem.chunks = [];

        for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
            const start = chunkIndex * chunkSize;
            const end = Math.min(start + chunkSize, file.size);

            queueItem.chunks.push({
                index: chunkIndex,
                start: start,
                end: end,
                size: end - start,
                status: 'pending'
            });
        }

        console.log(`UniversalFileUploader: 文件 ${file.name} 分块完成，共 ${totalChunks} 块`);
    }

    async processUploadQueue() {
        while (this.uploadQueue.length > 0 &&
               this.activeUploads.size < this.options.maxConcurrentUploads) {

            const queueItem = this.uploadQueue.shift();
            if (queueItem && queueItem.status === 'queued') {
                this.startFileUpload(queueItem);
            }
        }
    }

    async startFileUpload(queueItem) {
        queueItem.status = 'uploading';
        queueItem.startTime = Date.now();

        this.activeUploads.set(queueItem.id, queueItem);

        // 触发上传开始事件
        this.emitFileEvent('uploadStarted', queueItem);

        try {
            if (this.options.enableChunking && queueItem.totalChunks > 1) {
                await this.uploadFileChunked(queueItem);
            } else {
                await this.uploadFileSingle(queueItem);
            }

            queueItem.status = 'completed';
            queueItem.endTime = Date.now();
            queueItem.progress = 100;

            // 触发上传完成事件
            this.emitFileEvent('uploadCompleted', queueItem);

            console.log(`UniversalFileUploader: 文件 ${queueItem.file.name} 上传完成`);
        } catch (error) {
            queueItem.status = 'error';
            queueItem.error = error.message;

            // 触发上传错误事件
            this.emitFileEvent('uploadError', { ...queueItem, error: error });

            console.error(`UniversalFileUploader: 文件 ${queueItem.file.name} 上传失败`, error);
        } finally {
            this.activeUploads.delete(queueItem.id);
            this.processUploadQueue(); // 处理队列中的下一个文件
        }
    }

    async uploadFileSingle(queueItem) {
        const formData = new FormData();
        formData.append('file', queueItem.file);
        formData.append('fileId', queueItem.id);
        formData.append('chunked', 'false');
        formData.append('totalChunks', 1);
        formData.append('chunkIndex', 0);

        const xhr = new XMLHttpRequest();

        return new Promise((resolve, reject) => {
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const progress = (event.loaded / event.total) * 100;
                    queueItem.progress = progress;
                    this.emitFileEvent('uploadProgress', queueItem);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        queueItem.response = response;
                        resolve(response);
                    } catch (error) {
                        reject(new Error('响应解析失败'));
                    }
                } else {
                    reject(new Error(`上传失败: ${xhr.status} ${xhr.statusText}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('网络错误'));
            });

            xhr.addEventListener('abort', () => {
                reject(new Error('上传已取消'));
            });

            xhr.open('POST', this.options.uploadUrl);
            xhr.send(formData);

            queueItem.xhr = xhr;
        });
    }

    async uploadFileChunked(queueItem) {
        for (const chunk of queueItem.chunks) {
            if (chunk.status !== 'pending') continue;

            try {
                await this.uploadChunk(queueItem, chunk);
                chunk.status = 'completed';
                queueItem.uploadedChunks++;

                // 更新总进度
                const overallProgress = (queueItem.uploadedChunks / queueItem.totalChunks) * 100;
                queueItem.progress = overallProgress;

                this.emitFileEvent('uploadProgress', queueItem);
                this.emitFileEvent('chunkCompleted', { ...queueItem, chunk });

            } catch (error) {
                chunk.status = 'error';
                chunk.error = error.message;
                throw error;
            }
        }

        // 所有分块上传完成，通知服务器合并
        await this.mergeChunks(queueItem);
    }

    async uploadChunk(queueItem, chunk) {
        const fileChunk = queueItem.file.slice(chunk.start, chunk.end);
        const formData = new FormData();

        formData.append('file', fileChunk);
        formData.append('fileId', queueItem.id);
        formData.append('chunked', 'true');
        formData.append('totalChunks', queueItem.totalChunks);
        formData.append('chunkIndex', chunk.index);
        formData.append('originalName', queueItem.file.name);
        formData.append('fileSize', queueItem.file.size);

        const response = await fetch(this.options.uploadUrl, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`分块上传失败: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        return result;
    }

    async mergeChunks(queueItem) {
        const mergeData = {
            fileId: queueItem.id,
            fileName: queueItem.file.name,
            fileSize: queueItem.file.size,
            totalChunks: queueItem.totalChunks,
            mimeType: queueItem.file.type
        };

        const response = await fetch('/api/rag/merge-chunks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mergeData)
        });

        if (!response.ok) {
            throw new Error(`分块合并失败: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        queueItem.mergeResult = result;

        return result;
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

    emitFileEvent(event, data) {
        if (this.eventListeners && this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`UniversalFileUploader: 事件 ${event} 处理错误`, error);
                }
            });
        }
    }

    // 进度跟踪
    getOverallProgress() {
        const allItems = [...this.uploadQueue, ...Array.from(this.activeUploads.values())];
        if (allItems.length === 0) return 100;

        const totalProgress = allItems.reduce((sum, item) => sum + item.progress, 0);
        return totalProgress / allItems.length;
    }

    getQueueStatus() {
        return {
            queued: this.uploadQueue.length,
            active: this.activeUploads.size,
            total: this.uploadQueue.length + this.activeUploads.size,
            overallProgress: this.getOverallProgress()
        };
    }

    // 文件管理
    cancelUpload(fileId) {
        // 取消队列中的文件
        const queueIndex = this.uploadQueue.findIndex(item => item.id === fileId);
        if (queueIndex !== -1) {
            const [cancelledItem] = this.uploadQueue.splice(queueIndex, 1);
            this.emitFileEvent('uploadCancelled', cancelledItem);
            return true;
        }

        // 取消正在上传的文件
        const activeItem = this.activeUploads.get(fileId);
        if (activeItem) {
            if (activeItem.xhr) {
                activeItem.xhr.abort();
            }
            activeItem.status = 'cancelled';
            this.activeUploads.delete(fileId);
            this.emitFileEvent('uploadCancelled', activeItem);
            this.processUploadQueue();
            return true;
        }

        return false;
    }

    pauseUpload(fileId) {
        const activeItem = this.activeUploads.get(fileId);
        if (activeItem && activeItem.xhr) {
            activeItem.xhr.abort();
            activeItem.status = 'paused';
            this.uploadQueue.unshift(activeItem);
            this.activeUploads.delete(fileId);
            this.emitFileEvent('uploadPaused', activeItem);
            this.processUploadQueue();
            return true;
        }
        return false;
    }

    resumeUpload(fileId) {
        const queueIndex = this.uploadQueue.findIndex(item => item.id === fileId);
        if (queueIndex !== -1) {
            const [item] = this.uploadQueue.splice(queueIndex, 1);
            item.status = 'queued';
            this.processUploadQueue();
            return true;
        }
        return false;
    }

    removeFromQueue(fileId) {
        const removed = this.cancelUpload(fileId) ||
                       this.uploadQueue.some((item, index) => {
                           if (item.id === fileId) {
                               this.uploadQueue.splice(index, 1);
                               this.emitFileEvent('fileRemoved', item);
                               return true;
                           }
                           return false;
                       });

        return removed;
    }

    clearQueue() {
        // 取消所有活跃上传
        this.activeUploads.forEach((item, fileId) => {
            this.cancelUpload(fileId);
        });

        // 清空队列
        const clearedItems = [...this.uploadQueue];
        this.uploadQueue = [];

        clearedItems.forEach(item => {
            this.emitFileEvent('fileRemoved', item);
        });

        console.log('UniversalFileUploader: 队列已清空');
        return clearedItems.length;
    }

    // 工具方法
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getFileIcon(fileType) {
        const iconMap = {
            // 文档
            'pdf': '📄',
            'word': '📝',
            'excel': '📊',
            'powerpoint': '📑',
            'text': '📃',

            // 代码
            'code': '💻',
            'script': '📜',

            // 图片
            'image': '🖼️',

            // 音频
            'audio': '🎵',

            // 视频
            'video': '🎬',

            // 数据
            'data': '📈',

            // 压缩
            'archive': '📦',

            // 默认
            'default': '📎'
        };

        if (fileType.includes('pdf')) return iconMap.pdf;
        if (fileType.includes('word')) return iconMap.word;
        if (fileType.includes('excel') || fileType.includes('spreadsheet')) return iconMap.excel;
        if (fileType.includes('powerpoint') || fileType.includes('presentation')) return iconMap.powerpoint;
        if (fileType.includes('text')) return iconMap.text;
        if (fileType.includes('image')) return iconMap.image;
        if (fileType.includes('audio')) return iconMap.audio;
        if (fileType.includes('video')) return iconMap.video;
        if (fileType.includes('zip') || fileType.includes('rar') || fileType.includes('tar')) return iconMap.archive;

        // 代码文件类型
        const codeTypes = ['javascript', 'python', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'html', 'css', 'json', 'xml'];
        if (codeTypes.some(type => fileType.includes(type))) return iconMap.code;

        return iconMap.default;
    }

    showInvalidFilesError(invalidFiles) {
        const errorList = invalidFiles.map(file =>
            `• ${file.name} (${this.formatFileSize(file.size)}) - ${this.getFileRejectionReason(file)}`
        ).join('\n');

        const errorMessage = `以下文件无法上传:\n${errorList}`;

        // 触发错误事件
        this.emitFileEvent('validationError', {
            files: invalidFiles,
            message: errorMessage
        });

        console.warn('UniversalFileUploader: 无效文件检测', invalidFiles);
    }

    getFileRejectionReason(file) {
        if (file.size > this.options.maxFileSize) {
            return `文件过大 (最大 ${this.formatFileSize(this.options.maxFileSize)})`;
        }

        if (!this.isFileTypeSupported(file)) {
            return '文件类型不支持';
        }

        if (!this.validateFileName(file.name)) {
            return '文件名无效';
        }

        return '未知原因';
    }

    // 销毁方法
    destroy() {
        this.clearQueue();

        // 移除事件监听器
        document.removeEventListener('dragover', this.handleDragOver);
        document.removeEventListener('drop', this.handleDrop);
        document.removeEventListener('dragleave', this.handleDragLeave);

        this.isInitialized = false;
        console.log('UniversalFileUploader: 已销毁');
    }
}

// 全局访问
window.UniversalFileUploader = UniversalFileUploader;
console.log('file-uploader.js: 通用文件上传器加载完成');