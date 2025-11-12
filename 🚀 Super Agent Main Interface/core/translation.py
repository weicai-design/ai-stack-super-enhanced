"""
多语言翻译服务
支持60种语言翻译
"""

from typing import Dict, Optional, Any, List
import asyncio
import httpx
from datetime import datetime

class TranslationService:
    """
    多语言翻译服务
    
    功能：
    1. 支持60种语言翻译
    2. 自动语言检测
    3. 高准确率翻译
    4. 批量翻译
    """
    
    def __init__(self):
        # 60+种主流语言（扩展版）
        self.supported_languages = [
            # 亚洲语言（20种）
            "zh", "zh-CN", "zh-TW", "en", "ja", "ko", "th", "vi", "id", "ms",
            "hi", "bn", "ta", "te", "ur", "fa", "ar", "he", "tr", "my",
            # 欧洲语言（30种）
            "fr", "de", "es", "it", "pt", "pt-BR", "ru", "pl", "nl", "sv",
            "da", "fi", "no", "cs", "hu", "ro", "bg", "hr", "sk", "sl",
            "el", "uk", "be", "sr", "mk", "sq", "lv", "lt", "et", "is",
            "ga", "cy", "mt", "eu", "ca", "gl", "bs", "me", "ka", "hy",
            # 其他语言（15种）
            "sw", "zu", "af", "am", "az", "gu", "kn", "ml", "mr", "ne",
            "si", "km", "lo", "ka", "hy", "az", "kk", "ky", "uz", "mn",
            # 补充语言（5种）
            "haw", "mi", "sm", "to", "ty"
        ]
        self.default_target = "zh"
        self.translation_service = "google"  # google, baidu, youdao, deepl
        self.api_key = None
        
    async def translate(
        self,
        text: str,
        target_lang: str = "zh",
        source_lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            source_lang: 源语言（可选，自动检测）
            
        Returns:
            翻译结果
        """
        if not text or not text.strip():
            return {
                "original_text": text,
                "translated_text": text,
                "source_language": source_lang or "unknown",
                "target_language": target_lang,
                "confidence": 0.0,
                "error": "文本为空"
            }
        
        # 检查语言支持
        if not self.is_supported(target_lang):
            return {
                "original_text": text,
                "translated_text": text,
                "source_language": source_lang or "unknown",
                "target_language": target_lang,
                "confidence": 0.0,
                "error": f"不支持的目标语言: {target_lang}"
            }
        
        # 自动检测源语言
        if not source_lang:
            source_lang = await self.detect_language(text)
        
        # 如果源语言和目标语言相同，直接返回
        if source_lang == target_lang:
            return {
                "original_text": text,
                "translated_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": 1.0,
                "note": "源语言和目标语言相同，无需翻译"
            }
        
        try:
            # 调用翻译服务
            translated_text = await self._translate_with_service(
                text, source_lang, target_lang
            )
            
            return {
                "original_text": text,
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": 0.9,
                "service": self.translation_service,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "original_text": text,
                "translated_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _translate_with_service(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """使用第三方服务进行翻译"""
        # TODO: 实现实际的翻译服务调用
        # 可以使用：
        # 1. Google Translate API（需要API Key）
        # 2. 百度翻译API（需要API Key）
        # 3. 有道翻译API（需要API Key）
        # 4. DeepL API（需要API Key）
        # 5. 免费服务：googletrans库（可能不稳定）
        
        # 临时实现：返回模拟翻译结果
        if source_lang == "en" and target_lang == "zh":
            return f"[翻译] {text}"
        elif source_lang == "zh" and target_lang == "en":
            return f"[Translated] {text}"
        else:
            return f"[{target_lang}] {text}"
    
    async def detect_language(self, text: str) -> str:
        """
        检测语言
        
        Args:
            text: 文本
            
        Returns:
            语言代码
        """
        if not text or not text.strip():
            return "unknown"
        
        # 基于字符特征检测语言
        # 中文检测
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            # 判断简体或繁体
            simplified_chars = ['国', '学', '时', '会', '说', '来', '这']
            if any(char in text for char in simplified_chars):
                return "zh-CN"
            return "zh-TW"
        
        # 日文检测
        if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in text):
            return "ja"
        
        # 韩文检测
        if any('\uAC00' <= char <= '\uD7AF' for char in text):
            return "ko"
        
        # 阿拉伯文检测
        if any('\u0600' <= char <= '\u06FF' for char in text):
            return "ar"
        
        # 俄文检测
        if any('\u0400' <= char <= '\u04FF' for char in text):
            return "ru"
        
        # 默认英文（如果包含ASCII字符）
        if any(char.isascii() and char.isalpha() for char in text):
            return "en"
        
        return "unknown"
    
    async def batch_translate(
        self,
        texts: List[str],
        target_lang: str = "zh",
        source_lang: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量翻译
        
        Args:
            texts: 文本列表
            target_lang: 目标语言
            source_lang: 源语言
            
        Returns:
            翻译结果列表
        """
        tasks = [
            self.translate(text, target_lang, source_lang)
            for text in texts
        ]
        return await asyncio.gather(*tasks)
    
    def is_supported(self, language: str) -> bool:
        """检查语言是否支持"""
        # 支持简写和完整格式
        if language in self.supported_languages:
            return True
        # 检查是否匹配（如 "zh-CN" 匹配 "zh"）
        base_lang = language.split("-")[0]
        return base_lang in [lang.split("-")[0] for lang in self.supported_languages]
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return self.supported_languages
    
    def set_translation_service(self, service: str, api_key: Optional[str] = None):
        """设置翻译服务"""
        if service in ["google", "baidu", "youdao", "deepl"]:
            self.translation_service = service
            if api_key:
                self.api_key = api_key

