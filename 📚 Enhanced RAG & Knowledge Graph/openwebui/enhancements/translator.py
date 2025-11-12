"""
多语言翻译模块
支持10种语言的实时翻译
"""

import httpx
from typing import Dict, Any, Optional
import asyncio


class MultiLanguageTranslator:
    """多语言翻译器"""
    
    def __init__(self):
        # 支持的语言
        self.supported_languages = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "ar": "العربية",
            "es": "Español",
            "vi": "Tiếng Việt",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский"
        }
        
        # 使用本地Ollama进行翻译
        self.ollama_api = "http://localhost:11434"
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        翻译文本
        """
        if source_lang not in self.supported_languages:
            return {"success": False, "error": f"不支持的源语言: {source_lang}"}
        
        if target_lang not in self.supported_languages:
            return {"success": False, "error": f"不支持的目标语言: {target_lang}"}
        
        if source_lang == target_lang:
            return {"success": True, "translated_text": text, "source_lang": source_lang, "target_lang": target_lang}
        
        try:
            # 使用Ollama进行翻译
            prompt = self._build_translation_prompt(text, source_lang, target_lang)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_api}/api/generate",
                    json={
                        "model": "qwen2.5:7b",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    translated = data.get("response", "").strip()
                    
                    return {
                        "success": True,
                        "original_text": text,
                        "translated_text": translated,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "source_lang_name": self.supported_languages[source_lang],
                        "target_lang_name": self.supported_languages[target_lang]
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": f"[翻译失败] {text}"
            }
    
    async def auto_detect_and_translate(self, text: str, target_lang: str = "zh") -> Dict[str, Any]:
        """
        自动检测语言并翻译
        """
        # 简单的语言检测
        source_lang = self._detect_language(text)
        
        return await self.translate(text, source_lang, target_lang)
    
    async def batch_translate(self, texts: list, source_lang: str, target_lang: str) -> list:
        """
        批量翻译
        """
        tasks = [self.translate(text, source_lang, target_lang) for text in texts]
        results = await asyncio.gather(*tasks)
        return results
    
    def _build_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """构建翻译提示词"""
        source_name = self.supported_languages[source_lang]
        target_name = self.supported_languages[target_lang]
        
        prompt = f"""请将以下{source_name}文本翻译成{target_name}。
只返回翻译结果，不要添加任何解释或额外内容。

原文：
{text}

译文："""
        
        return prompt
    
    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        # 检测中文
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"
        
        # 检测日文
        if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return "ja"
        
        # 检测韩文
        if any('\uac00' <= char <= '\ud7af' for char in text):
            return "ko"
        
        # 检测阿拉伯文
        if any('\u0600' <= char <= '\u06ff' for char in text):
            return "ar"
        
        # 检测俄文
        if any('\u0400' <= char <= '\u04ff' for char in text):
            return "ru"
        
        # 默认英文
        return "en"
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.supported_languages

