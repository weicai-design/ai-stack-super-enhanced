"""
Open WebUI风格的语音接口
使用Web Speech API实现零配置、高质量的语音交互
"""
from typing import Dict, Any, Optional
import base64
import os


class OpenWebUIVoice:
    """
    Open WebUI风格的语音系统
    - Web Speech API（浏览器原生）
    - 零配置、即开即用
    - 高质量、多语言
    """
    
    def __init__(self):
        self.edge_tts_available = False
        
        # 检查Edge TTS（作为备用）
        try:
            import edge_tts
            self.edge_tts_available = True
            print("✅ Edge TTS可用（备用方案）")
        except:
            print("⚠️ Edge TTS不可用，将完全依赖浏览器API")
    
    async def text_to_speech_webui_style(
        self, 
        text: str, 
        voice: str = "zh-CN",
        rate: float = 1.0,
        pitch: float = 1.0
    ) -> Dict[str, Any]:
        """
        Open WebUI风格的TTS
        返回配置供前端Web Speech API使用
        """
        # 清理文本（移除特殊字符）
        clean_text = self._clean_text_for_speech(text)
        
        return {
            "success": True,
            "text": clean_text,
            "voice": voice,
            "rate": rate,
            "pitch": pitch,
            "method": "web_speech_api",
            "note": "使用浏览器原生语音API，质量高、速度快"
        }
    
    def _clean_text_for_speech(self, text: str) -> str:
        """清理文本，适合语音播报"""
        import re
        
        # 移除Markdown格式
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **粗体**
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __斜体__
        text = re.sub(r'`([^`]+)`', r'\1', text)        # `代码`
        text = re.sub(r'#+\s*', '', text)               # ## 标题
        
        # 移除链接
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # 移除列表标记
        text = text.replace('- ', '').replace('* ', '')
        text = text.replace('1. ', '第一、').replace('2. ', '第二、').replace('3. ', '第三、')
        
        # 移除表情符号和特殊标记
        text = re.sub(r'[✅❌📊💡🎯🔍📈💼🔔📤🧠⚡🎉]', '', text)
        
        # 移除多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 替换专业术语为口语
        replacements = {
            'API': '接口',
            'RAG': '知识检索',
            'TTS': '语音合成',
            'STT': '语音识别',
            'ERP': '企业管理系统'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def get_web_speech_config(self) -> Dict[str, Any]:
        """获取Web Speech API配置"""
        return {
            "voices": [
                {"lang": "zh-CN", "name": "中文（女声）", "default": True},
                {"lang": "zh-HK", "name": "中文（香港）"},
                {"lang": "en-US", "name": "English (US)"},
                {"lang": "ja-JP", "name": "日本語"},
            ],
            "default_rate": 1.0,
            "default_pitch": 1.0,
            "default_volume": 1.0
        }


# 全局实例
openwebui_voice = OpenWebUIVoice()

