"""
封号预测系统
预测内容发布后的封号风险
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

class BanPredictionSystem:
    """
    封号预测系统
    
    功能：
    1. 违规内容检测
    2. 风险评分算法
    3. 封号概率预测
    4. 安全建议
    5. 预发布审核
    """
    
    def __init__(self):
        self.violation_patterns = {
            "spam": ["刷量", "刷赞", "刷评论"],
            "fraud": ["诈骗", "虚假", "欺骗"],
            "pornography": ["色情", "低俗"],
            "violence": ["暴力", "血腥"],
            "politics": ["政治敏感"],
            "copyright": ["版权", "侵权"]
        }
    
    async def predict_ban_risk(
        self,
        content: str,
        content_type: str = "text",  # text, image, video
        platform: str = "douyin",
        user_history: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        预测封号风险
        
        Args:
            content: 内容
            content_type: 内容类型
            platform: 平台
            user_history: 用户历史记录
            
        Returns:
            封号风险预测结果
        """
        # 检测违规内容
        violations = await self._detect_violations(content, content_type)
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(violations, user_history)
        
        # 预测封号概率
        ban_probability = self._predict_ban_probability(risk_score, violations, user_history)
        
        return {
            "risk_score": risk_score,
            "ban_probability": ban_probability,
            "risk_level": self._get_risk_level(ban_probability),
            "violations": violations,
            "safety_suggestions": self._generate_safety_suggestions(violations, risk_score),
            "pre_release_review": self._generate_pre_release_review(violations, risk_score),
            "predicted_at": datetime.now().isoformat()
        }
    
    async def _detect_violations(
        self,
        content: str,
        content_type: str
    ) -> List[Dict[str, Any]]:
        """检测违规内容"""
        violations = []
        
        # 检测文本违规
        for violation_type, patterns in self.violation_patterns.items():
            for pattern in patterns:
                if pattern in content:
                    violations.append({
                        "type": violation_type,
                        "pattern": pattern,
                        "severity": "high" if violation_type in ["fraud", "pornography", "violence"] else "medium"
                    })
        
        return violations
    
    def _calculate_risk_score(
        self,
        violations: List[Dict],
        user_history: Optional[Dict]
    ) -> float:
        """计算风险评分"""
        base_score = 0.0
        
        # 基于违规内容计算
        for violation in violations:
            if violation.get("severity") == "high":
                base_score += 0.3
            else:
                base_score += 0.1
        
        # 基于用户历史调整
        if user_history:
            previous_violations = user_history.get("violations", 0)
            if previous_violations > 0:
                base_score += min(0.3, previous_violations * 0.1)
        
        return min(1.0, base_score)
    
    def _predict_ban_probability(
        self,
        risk_score: float,
        violations: List[Dict],
        user_history: Optional[Dict]
    ) -> float:
        """预测封号概率"""
        # 基础概率
        probability = risk_score * 0.7
        
        # 如果有严重违规，增加概率
        has_high_severity = any(v.get("severity") == "high" for v in violations)
        if has_high_severity:
            probability += 0.2
        
        # 如果用户有历史违规，增加概率
        if user_history and user_history.get("violations", 0) > 2:
            probability += 0.1
        
        return min(1.0, probability)
    
    def _get_risk_level(self, ban_probability: float) -> str:
        """获取风险等级"""
        if ban_probability < 0.2:
            return "low"
        elif ban_probability < 0.5:
            return "medium"
        elif ban_probability < 0.8:
            return "high"
        else:
            return "critical"
    
    def _generate_safety_suggestions(
        self,
        violations: List[Dict],
        risk_score: float
    ) -> List[str]:
        """生成安全建议"""
        suggestions = []
        
        if risk_score > 0.7:
            suggestions.append("⚠️ 高风险警告：")
            suggestions.append("1. 强烈建议修改或删除内容")
            suggestions.append("2. 内容存在严重违规风险")
            suggestions.append("3. 发布后可能立即被封号")
        elif risk_score > 0.4:
            suggestions.append("⚠️ 中等风险：")
            suggestions.append("1. 建议修改违规内容")
            suggestions.append("2. 删除敏感词汇")
            suggestions.append("3. 审查后再发布")
        else:
            suggestions.append("✅ 风险较低，可以发布")
            suggestions.append("1. 建议再次检查内容")
            suggestions.append("2. 确保符合平台规则")
        
        return suggestions
    
    def _generate_pre_release_review(
        self,
        violations: List[Dict],
        risk_score: float
    ) -> Dict[str, Any]:
        """生成预发布审核结果"""
        if risk_score > 0.7:
            review_result = "reject"
            review_message = "内容存在严重违规风险，建议拒绝发布"
        elif risk_score > 0.4:
            review_result = "review"
            review_message = "内容需要人工审核"
        else:
            review_result = "approve"
            review_message = "内容可以发布"
        
        return {
            "result": review_result,
            "message": review_message,
            "violations_count": len(violations),
            "risk_score": risk_score
        }

