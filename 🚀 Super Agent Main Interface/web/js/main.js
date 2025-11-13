/**
 * 主界面初始化脚本
 * 确保所有功能正确连接
 */

// 立即执行初始化（不等待DOMContentLoaded，因为可能已经加载完成）
(function() {
    console.log('🚀 AI-STACK 超级Agent主界面初始化...');
    console.log('文档状态:', document.readyState);
    
    function initializeApp() {
    
    // 检查所有必需的元素
    const requiredElements = {
        'chat-input': '输入框',
        'play-btn': '播放按钮',
        'square-btn': '停止按钮',
        'voice-btn': '语音按钮',
        'file-btn': '文件按钮',
        'search-icon-btn': '搜索按钮',
        'chat-messages': '消息容器',
        'model-selector': '模型选择器'
    };
    
    const missingElements = [];
    for (const [id, name] of Object.entries(requiredElements)) {
        const element = document.getElementById(id);
        if (!element) {
            missingElements.push(`${name} (${id})`);
            console.error(`❌ 缺少元素: ${name} (${id})`);
        } else {
            console.log(`✅ 找到元素: ${name} (${id})`);
        }
    }
    
    if (missingElements.length > 0) {
        console.error('缺少以下元素:', missingElements);
        alert('界面初始化失败：缺少必需的元素\n' + missingElements.join('\n'));
        return;
    }
    
    // 初始化所有功能模块
    try {
        // 初始化聊天功能 - 确保ChatManager已加载
        if (typeof ChatManager !== 'undefined') {
            window.chatManager = new ChatManager();
            console.log('✅ 聊天管理器已初始化');
        } else {
            console.warn('⚠️ ChatManager未定义，等待加载...');
            // 如果ChatManager未定义，等待一下再试
            setTimeout(() => {
                if (typeof ChatManager !== 'undefined') {
                    window.chatManager = new ChatManager();
                    console.log('✅ 聊天管理器延迟初始化成功');
                } else {
                    console.error('❌ ChatManager仍然未定义，请检查chat.js是否正确加载');
                }
            }, 500);
        }
        
        // 初始化备忘录功能（如果元素存在）
        const memoList = document.getElementById('memo-list');
        if (memoList && typeof MemoManager !== 'undefined') {
            try {
                window.memoManager = new MemoManager();
                console.log('✅ 备忘录管理器已初始化');
            } catch (e) {
                console.warn('⚠️ 备忘录管理器初始化失败:', e);
            }
        }
        
        // 初始化任务功能（如果元素存在）
        const taskList = document.getElementById('task-list');
        if (taskList && typeof TaskManager !== 'undefined') {
            try {
                window.taskManager = new TaskManager();
                console.log('✅ 任务管理器已初始化');
            } catch (e) {
                console.warn('⚠️ 任务管理器初始化失败:', e);
            }
        }
        
        // 初始化监控功能
        if (typeof MonitorManager !== 'undefined') {
            window.monitorManager = new MonitorManager();
            console.log('✅ 监控管理器已初始化');
        } else {
            console.warn('⚠️ MonitorManager未定义');
        }
        
        // 添加全局错误处理
        window.addEventListener('error', (e) => {
            console.error('全局错误:', e.error);
        });
        
        // 测试输入框功能
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('focus', () => {
                console.log('输入框获得焦点');
            });
            chatInput.addEventListener('input', (e) => {
                console.log('输入内容:', e.target.value);
            });
        }
        
        // 测试按钮点击
        const playBtn = document.getElementById('play-btn');
        if (playBtn) {
            playBtn.addEventListener('click', () => {
                console.log('播放按钮被点击');
            });
        }
        
        // 测试导航栏
        const navItems = document.querySelectorAll('.nav-item');
        console.log(`找到 ${navItems.length} 个导航项`);
        navItems.forEach((item, index) => {
            item.addEventListener('click', () => {
                const module = item.dataset.module;
                console.log(`导航项被点击: ${module}`);
            });
        });
        
        console.log('✅ 主界面初始化完成！');
        
        // 显示初始化成功提示
        setTimeout(() => {
            const welcomeMsg = document.createElement('div');
            welcomeMsg.className = 'message-item system-message';
            welcomeMsg.innerHTML = `
                <div class="message-content">
                    <p>✅ 界面初始化完成，所有功能已就绪！</p>
                </div>
                <span class="message-time">${new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}</span>
            `;
            const messagesContainer = document.getElementById('chat-messages');
            if (messagesContainer) {
                messagesContainer.appendChild(welcomeMsg);
            }
        }, 500);
        
    } catch (error) {
        console.error('初始化失败:', error);
        alert('界面初始化失败: ' + error.message);
    }
    }
    
    // 如果DOM已加载，立即执行；否则等待
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApp);
    } else {
        // DOM已加载，立即执行
        setTimeout(initializeApp, 100);
    }
})();

// 导出全局函数供其他脚本使用
window.showModal = function(title, content) {
    // 创建简单的弹窗
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    modal.innerHTML = `
        <div style="background: #2d2d30; padding: 20px; border-radius: 8px; max-width: 500px; color: #cccccc;">
            <h3 style="margin-bottom: 10px;">${title}</h3>
            <div>${content}</div>
            <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" 
                    style="margin-top: 15px; padding: 8px 16px; background: #0e639c; color: white; border: none; border-radius: 4px; cursor: pointer;">
                关闭
            </button>
        </div>
    `;
    document.body.appendChild(modal);
};






