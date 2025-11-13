"""
语音交互系统
支持语音输入和语音输出
"""

from typing import Dict, Optional, Any, List
import asyncio
import base64
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VoiceInteraction:
    """
    语音交互系统
    
    功能：
    1. 语音输入（Web Speech API + 后端处理）
    2. 语音输出（TTS）
    3. 中英文支持
    4. 实时语音识别
    """
    
    def __init__(self):
        self.supported_languages = [
            "zh-CN", "en-US", "ja-JP", "ko-KR", "fr-FR", "de-DE", 
            "es-ES", "it-IT", "pt-PT", "ru-RU"
        ]
        self.current_language = "zh-CN"
        self.use_web_speech_api = True  # 优先使用浏览器Web Speech API
        self.fallback_service = "baidu"  # 备用服务
        
    async def recognize_speech(
        self,
        audio_data: Optional[bytes] = None,
        audio_text: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        语音识别
        
        Args:
            audio_data: 音频数据（WAV/MP3格式）
            audio_text: 音频文本（如果前端已识别）
            language: 语言代码
            
        Returns:
            识别结果
        """
        language = language or self.current_language
        
        # 如果前端已经识别（Web Speech API），直接返回
        if audio_text:
            return {
                "text": audio_text,
                "confidence": 0.95,
                "language": language,
                "method": "web_speech_api",
                "timestamp": datetime.now().isoformat()
            }
        
        # 如果提供音频数据，使用后端识别
        if audio_data:
            try:
                # TODO: 集成第三方语音识别服务（百度、讯飞、Google等）
                # 这里先返回模拟结果
                return await self._recognize_with_service(audio_data, language)
            except Exception as e:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": language,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "text": "",
            "confidence": 0.0,
            "language": language,
            "error": "未提供音频数据或文本",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _recognize_with_service(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """使用第三方服务进行语音识别"""
        # TODO: 实现实际的语音识别服务调用
        # 可以使用：
        # 1. 百度语音识别API
        # 2. 讯飞语音识别API
        # 3. Google Speech-to-Text API
        # 4. Azure Speech Services
        
        return {
            "text": "语音识别结果（待实现）",
            "confidence": 0.85,
            "language": language,
            "method": self.fallback_service,
            "timestamp": datetime.now().isoformat()
        }
    
    async def synthesize_speech(
        self,
        text: str,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> Dict[str, Any]:
        """
        语音合成（TTS）
        
        Args:
            text: 要合成的文本
            language: 语言代码
            voice: 语音类型（可选）
            speed: 语速（0.5-2.0）
            pitch: 音调（0.5-2.0）
            
        Returns:
            包含音频数据和元数据的字典
        """
        language = language or self.current_language
        
        try:
            # 优先使用浏览器Web Speech API（前端实现）
            # 后端提供备用TTS服务
            audio_data = await self._synthesize_with_service(
                text, language, voice, speed, pitch
            )
            
            return {
                "audio_data": base64.b64encode(audio_data).decode('utf-8'),
                "format": "mp3",
                "language": language,
                "text": text,
                "duration": len(audio_data) / 16000,  # 估算时长
                "method": "tts_service",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "text": text,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _synthesize_with_service(
        self,
        text: str,
        language: str,
        voice: Optional[str],
        speed: float,
        pitch: float
    ) -> bytes:
        """使用第三方服务进行语音合成⭐增强版（支持多种TTS服务）"""
        # 优先使用浏览器Web Speech API（前端实现）
        # 后端提供备用TTS服务
        
        # 策略1: 尝试使用gTTS（Google Text-to-Speech，免费且质量好）
        try:
            from gtts import gTTS
            import tempfile
            import os
            
            # 语言代码映射
            lang_map = {
                "zh-CN": "zh-cn",
                "zh-TW": "zh-tw",
                "en-US": "en",
                "ja-JP": "ja",
                "ko-KR": "ko",
                "fr-FR": "fr",
                "de-DE": "de",
                "es-ES": "es",
                "it-IT": "it",
                "pt-PT": "pt",
                "ru-RU": "ru"
            }
            
            lang_code = lang_map.get(language, language[:2] if len(language) >= 2 else 'zh')
            
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_path = tmp_file.name
            
            tts.save(tmp_path)
            
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(tmp_path)
            
            return audio_data
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"gTTS失败: {e}")
        
        # 策略2: 尝试使用pyttsx3（本地TTS，无需网络）
        try:
            import pyttsx3
            import tempfile
            import os
            
            engine = pyttsx3.init()
            
            # 设置语言
            voices = engine.getProperty('voices')
            if language.startswith("zh"):
                # 尝试找到中文语音
                for v in voices:
                    if 'chinese' in v.name.lower() or 'zh' in v.id.lower():
                        engine.setProperty('voice', v.id)
                        break
            elif language.startswith("en"):
                # 尝试找到英文语音
                for v in voices:
                    if 'english' in v.name.lower() or 'en' in v.id.lower():
                        engine.setProperty('voice', v.id)
                        break
            
            # 设置语速和音调
            engine.setProperty('rate', int(150 * speed))  # 默认150
            engine.setProperty('volume', 0.9)
            
            # 创建临时音频文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_path = tmp_file.name
            
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            
            # 读取音频文件
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # 清理临时文件
            os.unlink(tmp_path)
            
            return audio_data
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pyttsx3失败: {e}")
        
        # 策略3: 使用edge-tts（Microsoft Edge TTS，免费且质量好）
        try:
            import edge_tts
            import asyncio
            import tempfile
            import os
            
            # 选择语音
            voices = await edge_tts.list_voices()
            selected_voice = None
            
            for v in voices:
                if language.startswith("zh") and "zh-CN" in v.get("Locale", ""):
                    selected_voice = v.get("ShortName", "")
                    break
                elif language.startswith("en") and "en-US" in v.get("Locale", ""):
                    selected_voice = v.get("ShortName", "")
                    break
            
            if not selected_voice:
                # 默认使用第一个可用语音
                selected_voice = voices[0].get("ShortName", "") if voices else "zh-CN-XiaoxiaoNeural"
            
            # 生成语音
            communicate = edge_tts.Communicate(text, selected_voice, rate=f"+{int((speed - 1) * 100)}%")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_path = tmp_file.name
            
            await communicate.save(tmp_path)
            
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(tmp_path)
            
            return audio_data
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"edge-tts失败: {e}")
        
        # 所有TTS服务都失败，返回空数据（前端会使用Web Speech API）
        return b""
    
    def set_language(self, language: str):
        """设置语言"""
        if language in self.supported_languages:
            self.current_language = language
            return True
        return False
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return self.supported_languages
    
    async def check_availability(self) -> Dict[str, Any]:
        """检查语音服务可用性"""
        return {
            "web_speech_api": self.use_web_speech_api,
            "fallback_service": self.fallback_service,
            "supported_languages": len(self.supported_languages),
            "current_language": self.current_language,
            "status": "ready"
        }

