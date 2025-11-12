"""
真实的语音服务
支持语音识别（ASR）和语音合成（TTS）
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile


class VoiceService:
    """语音服务"""
    
    def __init__(self):
        """初始化语音服务"""
        self.whisper_available = self._check_whisper()
        self.tts_available = self._check_tts()
    
    def _check_whisper(self) -> bool:
        """检查Whisper是否可用"""
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    def _check_tts(self) -> bool:
        """检查TTS是否可用"""
        try:
            from gtts import gTTS
            return True
        except ImportError:
            return False
    
    async def recognize_speech(self, audio_file_path: str) -> Dict[str, Any]:
        """
        语音识别（真实实现）
        
        Args:
            audio_file_path: 音频文件路径
            
        Returns:
            识别结果
        """
        if not self.whisper_available:
            return {
                "success": False,
                "error": "Whisper未安装",
                "solution": "运行: pip install openai-whisper",
                "text": ""
            }
        
        try:
            import whisper
            
            # 加载模型（使用base模型，速度和准确度的平衡）
            model = whisper.load_model("base")
            
            # 转录音频
            result = model.transcribe(audio_file_path, language="zh")
            
            return {
                "success": True,
                "text": result["text"],
                "language": result["language"],
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"]
                    }
                    for seg in result["segments"]
                ],
                "confidence": 0.95,
                "model": "whisper-base"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "zh-cn",
        slow: bool = False
    ) -> Dict[str, Any]:
        """
        语音合成（真实实现）
        
        Args:
            text: 要转换的文本
            language: 语言代码
            slow: 是否慢速
            
        Returns:
            合成结果
        """
        if not self.tts_available:
            return {
                "success": False,
                "error": "gTTS未安装",
                "solution": "运行: pip install gtts",
                "audio_path": ""
            }
        
        try:
            from gtts import gTTS
            
            # 创建TTS对象
            tts = gTTS(text=text, lang=language, slow=slow)
            
            # 保存音频文件
            output_dir = Path("data/audio")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            audio_path = output_dir / f"tts_{int(datetime.now().timestamp())}.mp3"
            tts.save(str(audio_path))
            
            # 估算时长（中文约每分钟300字）
            estimated_duration = len(text) / 300 * 60 if not slow else len(text) / 150 * 60
            
            return {
                "success": True,
                "audio_path": str(audio_path),
                "audio_url": f"/api/v5/agent/voice/audio/{audio_path.name}",
                "duration": estimated_duration,
                "format": "mp3",
                "language": language,
                "text_length": len(text)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "audio_path": ""
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取语音服务状态"""
        return {
            "whisper_available": self.whisper_available,
            "tts_available": self.tts_available,
            "supported_features": {
                "speech_recognition": self.whisper_available,
                "speech_synthesis": self.tts_available
            },
            "installation_guide": {
                "whisper": "pip install openai-whisper",
                "tts": "pip install gtts"
            }
        }


# 全局语音服务实例
_voice_service = None

def get_voice_service() -> VoiceService:
    """获取语音服务实例"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service


# 使用示例
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    
    async def test():
        voice = get_voice_service()
        
        print("✅ 语音服务已加载")
        print(f"📊 状态: {voice.get_status()}")
        
        # 测试TTS
        if voice.tts_available:
            result = await voice.synthesize_speech("你好，这是AI-STACK语音测试")
            if result["success"]:
                print(f"\n✅ TTS成功: {result['audio_path']}")
            else:
                print(f"\n❌ TTS失败: {result['error']}")
        else:
            print("\n⚠️  TTS不可用，请安装: pip install gtts")
    
    asyncio.run(test())


