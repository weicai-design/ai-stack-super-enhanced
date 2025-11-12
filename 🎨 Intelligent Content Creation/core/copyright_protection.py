"""
版权保护功能
防侵权检测和保护
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

class CopyrightProtection:
    """
    版权保护系统
    
    功能：
    1. 内容原创度检测
    2. 版权风险评估
    3. 侵权预警
    4. 安全建议
    """
    
    def __init__(self):
        self.risk_threshold = 0.7  # 风险阈值
    
    async def check_originality(
        self,
        content: str,
        compare_with: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        检测内容原创度
        
        Args:
            content: 待检测内容
            compare_with: 对比内容列表（可选）
            
        Returns:
            原创度检测结果
        """
        # TODO: 实现原创度检测
        # 使用文本相似度算法（如TF-IDF、BERT等）
        
        originality_score = 0.85  # 0-1之间，1表示完全原创
        
        return {
            "originality_score": originality_score,
            "risk_level": "low" if originality_score >= 0.8 else "medium" if originality_score >= 0.6 else "high",
            "similarity_matches": [],
            "recommendations": self._generate_protection_recommendations(originality_score),
            "checked_at": datetime.now().isoformat()
        }
    
    async def assess_copyright_risk(
        self,
        content: str,
        platform: str = "douyin"
    ) -> Dict[str, Any]:
        """
        评估版权风险
        
        Args:
            content: 内容
            platform: 发布平台
            
        Returns:
            风险评估结果
        """
        # 检测原创度
        originality = await self.check_originality(content)
        
        # 检测敏感内容
        sensitive_content = self._detect_sensitive_content(content)
        
        # 综合风险评估
        risk_score = self._calculate_risk_score(originality, sensitive_content)
        
        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "originality": originality,
            "sensitive_content": sensitive_content,
            "platform_specific_risks": self._get_platform_risks(platform),
            "protection_suggestions": self._generate_protection_suggestions(risk_score),
            "assessed_at": datetime.now().isoformat()
        }
    
    def _detect_sensitive_content(self, content: str) -> Dict[str, Any]:
        """检测敏感内容"""
        # TODO: 实现敏感内容检测
        return {
            "has_sensitive_words": False,
            "sensitive_words": [],
            "has_trademark": False,
            "trademarks": []
        }
    
    def _calculate_risk_score(
        self,
        originality: Dict,
        sensitive_content: Dict
    ) -> float:
        """计算风险分数"""
        originality_score = originality.get("originality_score", 1.0)
        risk_score = 1.0 - originality_score
        
        if sensitive_content.get("has_sensitive_words"):
            risk_score += 0.2
        
        if sensitive_content.get("has_trademark"):
            risk_score += 0.1
        
        return min(1.0, risk_score)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """获取风险等级"""
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.6:
            return "medium"
        else:
            return "high"
    
    def _get_platform_risks(self, platform: str) -> List[str]:
        """获取平台特定风险"""
        platform_risks = {
            "douyin": [
                "内容重复检测严格",
                "版权保护机制完善",
                "建议使用原创内容"
            ],
            "xiaohongshu": [
                "图片版权要求高",
                "文字内容需原创",
                "避免使用他人图片"
            ]
        }
        return platform_risks.get(platform, [])
    
    def _generate_protection_recommendations(self, originality_score: float) -> List[str]:
        """生成保护建议"""
        recommendations = []
        
        if originality_score < 0.8:
            recommendations.append("原创度较低，建议：")
            recommendations.append("1. 增加原创内容比例")
            recommendations.append("2. 改写相似内容")
            recommendations.append("3. 添加个人观点和见解")
        
        recommendations.append("4. 使用原创图片和视频")
        recommendations.append("5. 标注内容来源（如引用）")
        
        return recommendations
    
    def _generate_protection_suggestions(self, risk_score: float) -> List[str]:
        """生成保护建议"""
        suggestions = []
        
        if risk_score > self.risk_threshold:
            suggestions.append("⚠️ 高风险警告：")
            suggestions.append("1. 建议重新创作内容")
            suggestions.append("2. 避免使用受版权保护的内容")
            suggestions.append("3. 使用原创素材")
        elif risk_score > 0.5:
            suggestions.append("⚠️ 中等风险：")
            suggestions.append("1. 建议修改相似部分")
            suggestions.append("2. 增加原创元素")
        else:
            suggestions.append("✅ 风险较低，可以发布")
        
        return suggestions

