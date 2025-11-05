/**
 * 语音录制和复听功能
 */

let audioRecorder = null;
let audioChunks = [];
let isRecording = false;

// 开始录音
async function startVoiceRecord() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioRecorder = new MediaRecorder(stream);
        audioChunks = [];
        isRecording = true;
        
        audioRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        audioRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await processVoiceInput(audioBlob);
            
            // 停止所有音频轨道
            stream.getTracks().forEach(track => track.stop());
            isRecording = false;
        };
        
        audioRecorder.start();
        updateVoiceButtonState(true);
        updateStatus("🎤 正在录音... 再次点击停止");
        
    } catch (error) {
        console.error("麦克风访问失败:", error);
        alert("无法访问麦克风，请检查浏览器权限设置");
        isRecording = false;
    }
}

// 停止录音
function stopVoiceRecord() {
    if (audioRecorder && audioRecorder.state === "recording") {
        audioRecorder.stop();
        updateVoiceButtonState(false);
    }
}

// 切换录音状态
function toggleVoiceRecord() {
    if (isRecording) {
        stopVoiceRecord();
    } else {
        startVoiceRecord();
    }
}

// 更新语音按钮状态
function updateVoiceButtonState(recording) {
    const btn = document.getElementById('voiceBtn');
    if (btn) {
        if (recording) {
            btn.classList.add('recording');
            btn.innerHTML = '🔴 录音中...';
        } else {
            btn.classList.remove('recording');
            btn.innerHTML = '🎤 语音输入';
        }
    }
}

// 处理语音输入
async function processVoiceInput(audioBlob) {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'voice.wav');
    
    try {
        updateStatus("🔄 正在识别语音...");
        
        const response = await fetch('/api/voice/stt', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 显示识别结果
            const recognizedText = result.text;
            document.getElementById('userInput').value = recognizedText;
            
            // 保存音频供复听
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // 添加可复听的消息
            addVoiceMessage(recognizedText, audioUrl, true);
            
            updateStatus("✅ 语音识别完成: " + recognizedText.substring(0, 20) + "...");
        } else {
            alert("语音识别失败: " + (result.error || "未知错误"));
            updateStatus("❌ 语音识别失败");
        }
    } catch (error) {
        console.error("语音处理失败:", error);
        alert("处理失败: " + error.message);
        updateStatus("❌ 处理失败");
    }
}

// 添加可复听的语音消息
function addVoiceMessage(text, audioUrl, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'message-user' : 'message-ai'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 语音播放按钮
    const audioControl = document.createElement('button');
    audioControl.className = 'audio-play-btn';
    audioControl.innerHTML = '🔊 播放语音';
    audioControl.onclick = () => playAudio(audioUrl, audioControl);
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMessage(text);
    
    contentDiv.appendChild(audioControl);
    contentDiv.appendChild(textDiv);
    
    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';
    metaDiv.textContent = new Date().toLocaleTimeString('zh-CN');
    contentDiv.appendChild(metaDiv);
    
    messageDiv.appendChild(contentDiv);
    
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 播放音频
function playAudio(audioUrl, button) {
    const audio = new Audio(audioUrl);
    const originalText = button.innerHTML;
    
    button.innerHTML = '⏸️ 播放中...';
    button.disabled = true;
    
    audio.onended = () => {
        button.innerHTML = originalText;
        button.disabled = false;
    };
    
    audio.onerror = () => {
        button.innerHTML = originalText;
        button.disabled = false;
        alert("音频播放失败");
    };
    
    audio.play();
}

// 重新定义toggleVoice函数（覆盖index.html中的）
window.toggleVoice = toggleVoiceRecord;

