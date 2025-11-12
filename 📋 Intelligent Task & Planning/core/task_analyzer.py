"""
任务分析器
智能分析任务，提供执行建议
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import re

class TaskAnalyzer:
    """
    任务分析器
    
    功能：
    1. 分析任务复杂度
    2. 估算执行时间
    3. 识别所需资源
    4. 提供执行建议
    """
    
    def __init__(self):
        self.complexity_indicators = {
            "simple": ["简单", "快速", "直接"],
            "medium": ["一般", "标准", "常规"],
            "complex": ["复杂", "困难", "挑战"],
            "very_complex": ["非常复杂", "极其困难", "重大"]
        }
    
    async def analyze_task(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析任务
        
        Args:
            task: 任务信息
            
        Returns:
            分析结果
        """
        description = task.get("description", "")
        title = task.get("title", "")
        
        # 分析复杂度
        complexity = self._analyze_complexity(description, title)
        
        # 估算执行时间
        estimated_time = self._estimate_time(complexity, description)
        
        # 识别所需资源
        required_resources = self._identify_resources(description)
        
        # 识别依赖
        dependencies = self._identify_dependencies(description)
        
        # 生成建议
        suggestions = self._generate_suggestions(complexity, required_resources)
        
        return {
            "complexity": complexity,
            "estimated_time_hours": estimated_time,
            "required_resources": required_resources,
            "dependencies": dependencies,
            "suggestions": suggestions,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _analyze_complexity(self, description: str, title: str) -> str:
        """分析复杂度"""
        text = f"{description} {title}".lower()
        
        # 检查关键词
        if any(keyword in text for keyword in self.complexity_indicators["very_complex"]):
            return "very_complex"
        elif any(keyword in text for keyword in self.complexity_indicators["complex"]):
            return "complex"
        elif any(keyword in text for keyword in self.complexity_indicators["simple"]):
            return "simple"
        else:
            return "medium"
    
    def _estimate_time(self, complexity: str, description: str) -> float:
        """估算执行时间（小时）"""
        base_times = {
            "simple": 0.5,
            "medium": 2.0,
            "complex": 8.0,
            "very_complex": 24.0
        }
        
        base_time = base_times.get(complexity, 2.0)
        
        # 根据描述长度调整
        length_factor = min(len(description) / 100, 2.0)
        
        return base_time * length_factor
    
    def _identify_resources(self, description: str) -> List[str]:
        """识别所需资源"""
        resources = []
        text = description.lower()
        
        if any(keyword in text for keyword in ["数据库", "数据", "查询"]):
            resources.append("database")
        
        if any(keyword in text for keyword in ["API", "接口", "服务"]):
            resources.append("api")
        
        if any(keyword in text for keyword in ["文件", "文档", "上传"]):
            resources.append("file_storage")
        
        if any(keyword in text for keyword in ["计算", "处理", "分析"]):
            resources.append("compute")
        
        return resources
    
    def _identify_dependencies(self, description: str) -> List[str]:
        """识别依赖"""
        dependencies = []
        text = description.lower()
        
        # 检查是否有依赖关键词
        dep_patterns = [
            r"依赖(.+?)(?:。|$)",
            r"需要(.+?)完成",
            r"基于(.+?)",
            r"在(.+?)之后"
        ]
        
        for pattern in dep_patterns:
            matches = re.findall(pattern, text)
            dependencies.extend(matches)
        
        return dependencies
    
    def _generate_suggestions(
        self,
        complexity: str,
        resources: List[str]
    ) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if complexity == "very_complex":
            suggestions.append("建议将任务分解为多个子任务")
            suggestions.append("建议分阶段执行")
        
        if "database" in resources:
            suggestions.append("确保数据库连接正常")
            suggestions.append("考虑使用事务保证数据一致性")
        
        if "api" in resources:
            suggestions.append("检查API可用性")
            suggestions.append("准备错误处理和重试机制")
        
        if complexity in ["complex", "very_complex"]:
            suggestions.append("建议先进行小规模测试")
            suggestions.append("准备回滚方案")
        
        return suggestions

