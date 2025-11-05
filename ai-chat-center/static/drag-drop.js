/**
 * 文件拖拽上传功能
 */

// 初始化拖拽功能
function initDragDrop() {
    const dropZone = document.querySelector('.chat-container');
    const chatInput = document.getElementById('userInput');
    
    // 阻止默认拖拽行为
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // 拖拽进入高亮
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        dropZone.classList.add('drag-over');
        showDropHint();
    }
    
    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
        hideDropHint();
    }
    
    // 处理文件放下
    dropZone.addEventListener('drop', handleDrop, false);
    
    async function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            await handleFiles(files);
        }
    }
}

// 显示拖拽提示
function showDropHint() {
    let hint = document.getElementById('dropHint');
    if (!hint) {
        hint = document.createElement('div');
        hint.id = 'dropHint';
        hint.className = 'drop-hint';
        hint.innerHTML = '📎 松开鼠标上传文件';
        document.body.appendChild(hint);
    }
    hint.style.display = 'block';
}

// 隐藏拖拽提示
function hideDropHint() {
    const hint = document.getElementById('dropHint');
    if (hint) {
        hint.style.display = 'none';
    }
}

// 处理多个文件
async function handleFiles(files) {
    for (let file of files) {
        await uploadSingleFile(file);
    }
}

// 上传单个文件
async function uploadSingleFile(file) {
    updateStatus(`📤 正在上传: ${file.name}`);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', 'user_001');
    
    try {
        const response = await fetch('/api/file/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            addMessage(`✅ 已上传文件: ${file.name}\n类型: ${result.format}\n大小: ${(result.size / 1024).toFixed(2)} KB`, true);
            
            if (result.type === 'text' && result.content) {
                addMessage(`📄 文件内容预览:\n${result.content.substring(0, 300)}${result.content.length > 300 ? '...' : ''}`, false);
                
                if (result.rag_saved) {
                    addMessage(`💾 文件已保存到知识库，可以向我提问相关内容`, false);
                }
            }
            
            updateStatus("✅ 文件上传成功");
        } else {
            addMessage(`❌ 上传失败: ${result.error}`, false);
            updateStatus("❌ 上传失败");
        }
    } catch (error) {
        addMessage(`❌ 上传出错: ${error.message}`, false);
        updateStatus("❌ 上传出错");
    }
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDragDrop);
} else {
    initDragDrop();
}

