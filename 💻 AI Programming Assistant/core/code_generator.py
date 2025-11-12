"""
代码生成器
支持25种编程语言
"""

from typing import Dict, List, Optional, Any
import asyncio
from .llm_code_generator import LLMCodeGenerator

class CodeGenerator:
    """
    代码生成器
    
    功能：
    1. 自然语言生成代码
    2. 支持25种语言
    3. 函数/类/模块生成
    4. API接口生成
    5. 测试代码生成
    """
    
    def __init__(self, model: str = "gpt-4"):
        self.supported_languages = [
            "python", "javascript", "typescript", "java", "cpp", "c", "csharp",
            "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "r",
            "sql", "html", "css", "shell", "powershell", "lua", "perl",
            "dart", "haskell", "elixir"
        ]
        self.llm_generator = LLMCodeGenerator(model)
    
    async def generate_code(
        self,
        description: str,
        language: str = "python",
        code_type: str = "function",  # function, class, module, api, test
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成代码
        
        Args:
            description: 代码描述
            language: 编程语言
            code_type: 代码类型
            context: 上下文信息
            
        Returns:
            生成的代码
        """
        if language not in self.supported_languages:
            return {
                "success": False,
                "error": f"不支持的语言: {language}"
            }
        
        # 使用LLM生成代码
        result = await self.llm_generator.generate_with_llm(
            prompt=description,
            language=language,
            code_type=code_type,
            context=context
        )
        
        return result
    
    async def generate_function(
        self,
        function_name: str,
        description: str,
        parameters: List[Dict[str, str]],
        return_type: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """生成函数"""
        return await self.generate_code(
            description=f"函数 {function_name}: {description}",
            language=language,
            code_type="function"
        )
    
    async def generate_class(
        self,
        class_name: str,
        description: str,
        methods: List[Dict[str, str]],
        language: str = "python"
    ) -> Dict[str, Any]:
        """生成类"""
        return await self.generate_code(
            description=f"类 {class_name}: {description}",
            language=language,
            code_type="class"
        )
    
    async def generate_api(
        self,
        endpoint: str,
        method: str,
        description: str,
        parameters: List[Dict[str, str]],
        language: str = "python"
    ) -> Dict[str, Any]:
        """生成API接口"""
        return await self.generate_code(
            description=f"API {method} {endpoint}: {description}",
            language=language,
            code_type="api"
        )

