"""
真实性验证管道
用于验证RAG检索结果的真实性和可信度
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


class TruthVerificationPipeline:
    """真实性验证管道"""
    
    def __init__(self, llm_client=None):
        """
        初始化真实性验证管道
        
        Args:
            llm_client: LLM客户端（可选，用于AI验证）
        """
        self.llm_client = llm_client
        self.verification_cache = {}
    
    def verify(self, text: str, sources: List[Dict] = None) -> Dict[str, Any]:
        """
        验证文本的真实性
        
        Args:
            text: 要验证的文本
            sources: 来源信息列表
        
        Returns:
            验证结果字典
        """
        result = {
            "text": text,
            "verified": False,
            "confidence_score": 0.0,
            "verification_details": {},
            "sources": sources or [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. 基础验证
        basic_score = self._basic_verification(text)
        result["verification_details"]["basic"] = basic_score
        
        # 2. 来源验证
        if sources:
            source_score = self._verify_sources(sources)
            result["verification_details"]["sources"] = source_score
        else:
            source_score = 0.5  # 无来源时中等可信度
        
        # 3. 一致性验证
        consistency_score = self._check_consistency(text, sources)
        result["verification_details"]["consistency"] = consistency_score
        
        # 4. 事实核查
        fact_score = self._fact_check(text)
        result["verification_details"]["facts"] = fact_score
        
        # 5. 时效性验证
        timeliness_score = self._check_timeliness(text, sources)
        result["verification_details"]["timeliness"] = timeliness_score
        
        # 计算综合置信度
        weights = {
            "basic": 0.2,
            "sources": 0.25,
            "consistency": 0.25,
            "facts": 0.2,
            "timeliness": 0.1
        }
        
        confidence = (
            basic_score * weights["basic"] +
            source_score * weights["sources"] +
            consistency_score * weights["consistency"] +
            fact_score * weights["facts"] +
            timeliness_score * weights["timeliness"]
        )
        
        result["confidence_score"] = round(confidence, 3)
        result["verified"] = confidence >= 0.7  # 70%以上认为可信
        
        # 生成验证建议
        result["suggestions"] = self._generate_suggestions(result)
        
        return result
    
    def _basic_verification(self, text: str) -> float:
        """基础验证：检查文本质量"""
        score = 1.0
        
        # 检查长度（太短或太长都降低可信度）
        length = len(text)
        if length < 10:
            score -= 0.3
        elif length > 10000:
            score -= 0.1
        
        # 检查是否包含可疑模式
        suspicious_patterns = [
            r'\b(假的|虚假|谣言|不实)\b',
            r'\b(据说|听说|可能)\b',
            r'\?\?\?',
            r'!!!+'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text):
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _verify_sources(self, sources: List[Dict]) -> float:
        """验证来源可信度"""
        if not sources:
            return 0.5
        
        total_score = 0.0
        
        for source in sources:
            source_score = 1.0
            
            # 检查来源类型
            source_type = source.get("type", "unknown")
            if source_type in ["academic", "official", "verified"]:
                source_score = 1.0
            elif source_type in ["news", "media"]:
                source_score = 0.8
            elif source_type in ["blog", "forum"]:
                source_score = 0.6
            else:
                source_score = 0.5
            
            # 检查是否有URL
            if source.get("url"):
                source_score += 0.1
            
            # 检查是否有作者
            if source.get("author"):
                source_score += 0.1
            
            # 检查是否有发布日期
            if source.get("published_date"):
                source_score += 0.1
            
            total_score += min(1.0, source_score)
        
        return total_score / len(sources)
    
    def _check_consistency(self, text: str, sources: List[Dict]) -> float:
        """检查文本与来源的一致性"""
        if not sources:
            return 0.7  # 无来源时假设中等一致性
        
        # 简化实现：检查关键词匹配
        text_keywords = set(self._extract_keywords(text))
        
        consistency_scores = []
        for source in sources:
            source_text = source.get("content", "")
            source_keywords = set(self._extract_keywords(source_text))
            
            if not source_keywords:
                continue
            
            # 计算关键词重叠率
            overlap = len(text_keywords & source_keywords)
            total = len(text_keywords | source_keywords)
            
            if total > 0:
                consistency = overlap / total
                consistency_scores.append(consistency)
        
        if not consistency_scores:
            return 0.7
        
        return sum(consistency_scores) / len(consistency_scores)
    
    def _fact_check(self, text: str) -> float:
        """事实核查"""
        score = 1.0
        
        # 检查是否包含数字和日期（可验证的事实）
        has_numbers = bool(re.search(r'\d+', text))
        has_dates = bool(re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?', text))
        
        if has_numbers or has_dates:
            score += 0.1  # 有具体数据，提高可信度
        
        # 检查是否包含不确定性词汇
        uncertain_words = ['可能', '也许', '大概', '估计', '听说', '据说']
        for word in uncertain_words:
            if word in text:
                score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _check_timeliness(self, text: str, sources: List[Dict]) -> float:
        """检查时效性"""
        if not sources:
            return 0.7
        
        now = datetime.now()
        timeliness_scores = []
        
        for source in sources:
            published_date = source.get("published_date")
            if not published_date:
                continue
            
            try:
                if isinstance(published_date, str):
                    pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                else:
                    pub_date = published_date
                
                # 计算时间差（天）
                days_diff = (now - pub_date).days
                
                # 越新越好
                if days_diff < 7:
                    timeliness = 1.0
                elif days_diff < 30:
                    timeliness = 0.9
                elif days_diff < 90:
                    timeliness = 0.8
                elif days_diff < 365:
                    timeliness = 0.7
                else:
                    timeliness = 0.6
                
                timeliness_scores.append(timeliness)
            except:
                continue
        
        if not timeliness_scores:
            return 0.7
        
        return sum(timeliness_scores) / len(timeliness_scores)
    
    def _extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """提取关键词（简单实现）"""
        # 移除标点和特殊字符
        text_clean = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词（简单按空格分）
        words = text_clean.split()
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '和', '与', '等', '及', 'the', 'a', 'an', 'and', 'or', 'but'}
        keywords = [w for w in words if len(w) > 1 and w.lower() not in stop_words]
        
        # 统计频率
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回高频词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_k]]
    
    def _generate_suggestions(self, result: Dict) -> List[str]:
        """生成验证建议"""
        suggestions = []
        
        confidence = result["confidence_score"]
        details = result["verification_details"]
        
        if confidence < 0.5:
            suggestions.append("⚠️ 可信度较低，建议进一步核实")
        
        if details.get("sources", 0) < 0.6:
            suggestions.append("💡 建议添加更多权威来源")
        
        if details.get("consistency", 0) < 0.6:
            suggestions.append("⚠️ 文本与来源一致性较低，请仔细核对")
        
        if details.get("timeliness", 0) < 0.6:
            suggestions.append("📅 信息可能较旧，建议查找最新资料")
        
        if not result.get("sources"):
            suggestions.append("📚 建议添加来源信息以提高可信度")
        
        if confidence >= 0.9:
            suggestions.append("✅ 信息可信度很高")
        
        return suggestions
    
    def batch_verify(self, texts: List[str], sources_list: List[List[Dict]] = None) -> List[Dict]:
        """批量验证"""
        results = []
        
        for i, text in enumerate(texts):
            sources = sources_list[i] if sources_list and i < len(sources_list) else None
            result = self.verify(text, sources)
            results.append(result)
        
        return results
    
    def get_verification_report(self, results: List[Dict]) -> Dict[str, Any]:
        """生成验证报告"""
        total = len(results)
        if total == 0:
            return {
                "total": 0,
                "verified": 0,
                "average_confidence": 0.0
            }
        
        verified_count = sum(1 for r in results if r["verified"])
        avg_confidence = sum(r["confidence_score"] for r in results) / total
        
        return {
            "total": total,
            "verified": verified_count,
            "unverified": total - verified_count,
            "verification_rate": round(verified_count / total, 3),
            "average_confidence": round(avg_confidence, 3),
            "high_confidence": sum(1 for r in results if r["confidence_score"] >= 0.9),
            "medium_confidence": sum(1 for r in results if 0.7 <= r["confidence_score"] < 0.9),
            "low_confidence": sum(1 for r in results if r["confidence_score"] < 0.7)
        }


# 全局实例
truth_verifier = TruthVerificationPipeline()
