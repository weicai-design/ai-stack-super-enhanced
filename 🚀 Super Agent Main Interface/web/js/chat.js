/**
 * 聊天功能
 * 实现AI工作流9步骤的前端交互
 */

const API_BASE = '/api/super-agent';

class ChatManager {
    constructor() {
        this.messages = [];
        this.currentContext = {};
        this.init();
    }

    init() {
        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');
        const voiceBtn = document.getElementById('voice-btn');
        const fileBtn = document.getElementById('file-btn');
        const searchBtn = document.getElementById('search-btn');

        sendBtn.addEventListener('click', () => this.sendMessage());
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        const translateBtn = document.getElementById('translate-btn');
        const generateBtn = document.getElementById('generate-btn');
        
        voiceBtn.addEventListener('click', () => this.startVoiceInput());
        fileBtn.addEventListener('click', () => this.toggleFileUpload());
        searchBtn.addEventListener('click', () => this.toggleSearchMode());
        translateBtn.addEventListener('click', () => this.translateText());
        generateBtn.addEventListener('click', () => this.generateFile());
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        // 显示用户消息
        this.addMessage('user', message);
        input.value = '';

        // 发送到后端
        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    input_type: 'text',
                    context: this.currentContext
                })
            });

            const result = await response.json();
            
            if (result.success) {
                const messageDiv = this.addMessage('assistant', result.response);
                
                // 更新上下文
                if (result.rag_retrievals) {
                    this.currentContext.rag_retrievals = result.rag_retrievals;
                }
                
                // 显示响应时间（2秒目标）
                if (result.response_time) {
                    const responseTime = result.response_time;
                    console.log(`响应时间: ${responseTime.toFixed(2)}秒`);
                    
                    // 如果超过2秒，显示警告
                    if (responseTime > 2.0) {
                        this.showWarning(`响应时间 ${responseTime.toFixed(2)}秒，超过2秒目标`);
                    }
                    
                    // 显示响应时间提示
                    const timeIndicator = document.createElement('span');
                    timeIndicator.className = 'response-time';
                    timeIndicator.textContent = `${responseTime.toFixed(2)}s`;
                    timeIndicator.style.color = responseTime > 2.0 ? '#f56c6c' : '#67c23a';
                    timeIndicator.style.fontSize = '12px';
                    timeIndicator.style.marginLeft = '10px';
                    messageDiv.appendChild(timeIndicator);
                }
                
                // 如果创建了备忘录，显示提示
                if (result.memo_created) {
                    this.showNotification('📝 已自动创建备忘录');
                }
                
                // 可选：自动语音输出（如果用户启用）
                if (localStorage.getItem('auto_voice_output') === 'true') {
                    this.synthesizeAndPlay(result.response);
                }
            } else {
                this.addMessage('assistant', `错误: ${result.error || '未知错误'}`);
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.addMessage('assistant', `发送失败: ${error.message}`);
        }
    }

    addMessage(role, content, options = {}) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // 如果是语音消息，添加播放按钮
        if (options.audioUrl) {
            const audioPlayer = document.createElement('audio');
            audioPlayer.src = options.audioUrl;
            audioPlayer.controls = true;
            audioPlayer.style.marginTop = '10px';
            messageDiv.appendChild(audioPlayer);
        }
        
        // 添加文本内容
        const textContent = document.createElement('div');
        textContent.textContent = content;
        messageDiv.appendChild(textContent);
        
        // 如果是助手消息，添加语音播放按钮
        if (role === 'assistant' && content.length > 10) {
            const voiceBtn = document.createElement('button');
            voiceBtn.className = 'voice-play-btn';
            voiceBtn.textContent = '🔊';
            voiceBtn.title = '播放语音';
            voiceBtn.onclick = () => this.synthesizeAndPlay(content);
            voiceBtn.style.marginLeft = '10px';
            voiceBtn.style.cursor = 'pointer';
            messageDiv.appendChild(voiceBtn);
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ role, content, timestamp: new Date(), options });
        return messageDiv;
    }
    
    async synthesizeAndPlay(text) {
        try {
            const response = await fetch(`${API_BASE}/voice/synthesize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    language: 'zh-CN',
                    speed: 1.0,
                    pitch: 1.0
                })
            });
            
            const result = await response.json();
            
            if (result.audio_data) {
                // 将base64音频数据转换为Blob URL
                const binaryString = atob(result.audio_data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: 'audio/mp3' });
                const audioUrl = URL.createObjectURL(blob);
                
                // 播放音频
                const audio = new Audio(audioUrl);
                audio.play();
                
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                };
            }
        } catch (error) {
            console.error('语音合成失败:', error);
        }
    }
    
    showNotification(message) {
        // 显示非交互类信息弹窗
        const modal = document.getElementById('modal-overlay');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = '通知';
        modalBody.textContent = message;
        modal.style.display = 'flex';
        
        // 3秒后自动关闭
        setTimeout(() => {
            modal.style.display = 'none';
        }, 3000);
    }
    
    showWarning(message) {
        console.warn(message);
        // 可以添加警告提示UI
    }

    async startVoiceInput() {
        const voiceBtn = document.getElementById('voice-btn');
        const chatInput = document.getElementById('chat-input');
        
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('您的浏览器不支持语音识别功能');
            return;
        }
        
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new Recognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = () => {
            voiceBtn.textContent = '🔴';
            voiceBtn.style.color = 'red';
            chatInput.placeholder = '正在聆听...';
        };
        
        recognition.onresult = async (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            chatInput.placeholder = '输入消息... (支持语音、文件、搜索)';
            
            // 可选：发送到后端进行二次识别和优化
            try {
                const response = await fetch(`${API_BASE}/voice/recognize`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ audio_text: transcript, language: 'zh-CN' })
                });
                const result = await response.json();
                if (result.text && result.text !== transcript) {
                    chatInput.value = result.text;
                }
            } catch (error) {
                console.error('语音识别优化失败:', error);
            }
        };
        
        recognition.onerror = (event) => {
            console.error('语音识别错误:', event.error);
            alert(`语音识别失败: ${event.error}`);
            voiceBtn.textContent = '🎤';
            voiceBtn.style.color = '';
            chatInput.placeholder = '输入消息... (支持语音、文件、搜索)';
        };
        
        recognition.onend = () => {
            voiceBtn.textContent = '🎤';
            voiceBtn.style.color = '';
            chatInput.placeholder = '输入消息... (支持语音、文件、搜索)';
        };
        
        recognition.start();
    }

    toggleFileUpload() {
        const uploadArea = document.getElementById('file-upload-area');
        uploadArea.style.display = uploadArea.style.display === 'none' ? 'block' : 'none';
        
        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }
    
    async handleFileUpload(event) {
        const files = Array.from(event.target.files);
        for (const file of files) {
            await this.uploadFile(file);
        }
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            this.addMessage('system', `文件 "${file.name}" 上传成功`);
        } catch (error) {
            console.error('文件上传失败:', error);
            this.addMessage('system', `文件 "${file.name}" 上传失败: ${error.message}`);
        }
    }

    async toggleSearchMode() {
        const chatInput = document.getElementById('chat-input');
        const currentText = chatInput.value.trim();
        
        if (!currentText) {
            chatInput.placeholder = '输入搜索关键词...';
            return;
        }
        
        // 执行搜索
        try {
            const response = await fetch(`${API_BASE}/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: currentText,
                    search_type: 'web',
                    max_results: 10
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.results && result.results.length > 0) {
                let searchResults = `🔍 搜索结果 (${result.total}条):\n\n`;
                result.results.slice(0, 5).forEach((item, index) => {
                    searchResults += `${index + 1}. ${item.title}\n   ${item.snippet}\n   ${item.url}\n\n`;
                });
                this.addMessage('assistant', searchResults);
            } else {
                this.addMessage('assistant', '未找到相关搜索结果');
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.addMessage('assistant', `搜索失败: ${error.message}`);
        }
    }
    
    async translateText() {
        const chatInput = document.getElementById('chat-input');
        const text = chatInput.value.trim();
        
        if (!text) {
            alert('请先输入要翻译的文本');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    target_lang: 'zh',
                    source_lang: null  // 自动检测
                })
            });
            
            const result = await response.json();
            
            if (result.translated_text) {
                this.addMessage('assistant', 
                    `🌐 翻译结果:\n原文 (${result.source_language}): ${result.original_text}\n译文 (${result.target_language}): ${result.translated_text}`
                );
            } else {
                this.addMessage('assistant', `翻译失败: ${result.error || '未知错误'}`);
            }
        } catch (error) {
            console.error('翻译失败:', error);
            this.addMessage('assistant', `翻译失败: ${error.message}`);
        }
    }
    
    async generateFile() {
        const chatInput = document.getElementById('chat-input');
        const content = chatInput.value.trim();
        
        if (!content) {
            alert('请先输入要生成文件的内容');
            return;
        }
        
        // 显示文件类型选择对话框
        const fileType = prompt('请选择文件类型:\n1. word\n2. excel\n3. pdf\n4. ppt', 'word');
        
        if (!fileType) return;
        
        try {
            const response = await fetch(`${API_BASE}/generate/file`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_type: fileType,
                    content: content,
                    title: '生成的文件'
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.file_data_base64) {
                // 下载文件
                const binaryString = atob(result.file_data_base64);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: `application/${result.format}` });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = result.filename;
                a.click();
                URL.revokeObjectURL(url);
                
                this.addMessage('assistant', `✅ 文件 "${result.filename}" 生成成功！`);
            } else {
                this.addMessage('assistant', `文件生成失败: ${result.error || '未知错误'}`);
            }
        } catch (error) {
            console.error('文件生成失败:', error);
            this.addMessage('assistant', `文件生成失败: ${error.message}`);
        }
    }
}

// 初始化聊天管理器
const chatManager = new ChatManager();

