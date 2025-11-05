"""
后端语音方案（备用）
如果浏览器API不行，使用这个
"""
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any


class BackendVoice:
    """后端语音处理（Edge TTS + Whisper）"""
    
    def __init__(self):
        self.edge_tts_available = False
        self.whisper_available = False
        self.faster_whisper_available = False
        
        # 检查Edge TTS
        try:
            import edge_tts
            self.edge_tts_available = True
            print("✅ Edge TTS 可用")
        except:
            print("❌ Edge TTS 不可用")
        
        # 检查Whisper
        try:
            import whisper
            self.whisper_available = True
            print("✅ Whisper 可用")
        except:
            print("❌ Whisper 不可用")
        
        # 检查Faster Whisper
        try:
            from faster_whisper import WhisperModel
            self.faster_whisper_available = True
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            print("✅ Faster Whisper 可用")
        except:
            print("❌ Faster Whisper 不可用")
    
    async def text_to_speech(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> Dict[str, Any]:
        """
        使用Edge TTS生成语音
        """
        if not self.edge_tts_available:
            return {
                "success": False,
                "error": "Edge TTS未安装",
                "install": "pip install edge-tts"
            }
        
        try:
            import edge_tts
            
            # 清理文本
            clean_text = self._clean_text(text)
            
            # 生成临时文件
            temp_dir = Path("static/audio")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = temp_dir / f"tts_{hash(clean_text)}.mp3"
            
            # 如果文件已存在，直接返回
            if output_file.exists():
                return {
                    "success": True,
                    "audio_url": f"/static/audio/{output_file.name}",
                    "cached": True
                }
            
            # 生成语音
            communicate = edge_tts.Communicate(clean_text, voice)
            await communicate.save(str(output_file))
            
            return {
                "success": True,
                "audio_url": f"/static/audio/{output_file.name}",
                "text": clean_text,
                "voice": voice
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def speech_to_text(self, audio_file_path: str) -> Dict[str, Any]:
        """
        使用Whisper识别语音
        """
        if self.faster_whisper_available:
            return self._faster_whisper_stt(audio_file_path)
        elif self.whisper_available:
            return self._whisper_stt(audio_file_path)
        else:
            return {
                "success": False,
                "error": "Whisper未安装",
                "install": "pip install openai-whisper 或 pip install faster-whisper"
            }
    
    def _faster_whisper_stt(self, audio_file_path: str) -> Dict[str, Any]:
        """使用Faster Whisper"""
        try:
            segments, info = self.whisper_model.transcribe(
                audio_file_path,
                language="zh",
                beam_size=5
            )
            
            text = "".join([segment.text for segment in segments])
            
            return {
                "success": True,
                "text": text.strip(),
                "language": info.language,
                "method": "faster_whisper"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _whisper_stt(self, audio_file_path: str) -> Dict[str, Any]:
        """使用标准Whisper"""
        try:
            import whisper
            
            model = whisper.load_model("base")
            result = model.transcribe(audio_file_path, language="zh")
            
            return {
                "success": True,
                "text": result["text"].strip(),
                "language": result.get("language", "zh"),
                "method": "whisper"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        import re
        
        # 移除Markdown
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'#+\s*', '', text)
        
        # 移除链接
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # 移除表情
        text = re.sub(r'[✅❌📊💡🎯🔍]', '', text)
        
        return text.strip()


# 全局实例
backend_voice = BackendVoice()

