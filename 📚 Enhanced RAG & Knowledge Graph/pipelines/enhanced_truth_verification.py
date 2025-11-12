"""
Enhanced Truth Verification Pipeline
增强的真实性验证管道

根据需求1.3：所有进入RAG库的信息都会进行去伪的处理，保证信息知识数据等的真实性和准确性

增强功能：
1. 信息来源验证
2. 内容一致性检查
3. 可信度评分系统
4. 自动去伪处理
5. 集成到摄入流程
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

# 尝试导入dateutil（可选依赖）
try:
    import dateutil.parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
    logger.warning("python-dateutil未安装，时间戳解析功能可能受限")

logger = logging.getLogger(__name__)


class TimestampValidator:
    """
    时间戳验证器
    验证信息时效性
    """
    
    def __init__(self, max_age_days: int = 365):
        """
        初始化时间戳验证器
        
        Args:
            max_age_days: 信息最大有效期（天数）
        """
        self.max_age_days = max_age_days
    
    def validate_timestamp(
        self, 
        timestamp: Optional[str], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        验证时间戳有效性
        
        Args:
            timestamp: 时间戳字符串（ISO格式或Unix时间戳）
            metadata: 元数据（可能包含日期信息）
            
        Returns:
            验证结果
        """
        if not timestamp and not metadata:
            return {
                "is_valid": True,  # 无时间戳时不拒绝
                "is_fresh": None,
                "age_days": None,
                "reason": "no_timestamp",
            }
        
        # 尝试从多个位置提取时间
        date_str = timestamp
        if not date_str and metadata:
            date_str = (
                metadata.get("date") or 
                metadata.get("published_date") or 
                metadata.get("timestamp") or
                metadata.get("created_at")
            )
        
        if not date_str:
            return {
                "is_valid": True,
                "is_fresh": None,
                "age_days": None,
                "reason": "no_date_found",
            }
        
        try:
            from datetime import datetime, timedelta
            import dateutil.parser
            
            # 解析日期
            if isinstance(date_str, (int, float)):
                # Unix时间戳
                parsed_date = datetime.fromtimestamp(date_str)
            else:
                # ISO格式或其他格式
                if HAS_DATEUTIL:
                    parsed_date = dateutil.parser.parse(str(date_str))
                else:
                    # 回退到简单解析（仅支持ISO格式）
                    try:
                        parsed_date = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
                    except ValueError:
                        # 如果ISO解析失败，尝试其他常见格式
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                            try:
                                parsed_date = datetime.strptime(str(date_str), fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            raise ValueError(f"无法解析日期格式: {date_str}")
            
            # 计算年龄
            now = datetime.now(parsed_date.tzinfo if parsed_date.tzinfo else None)
            age = now - parsed_date
            age_days = age.days
            
            # 检查是否过期
            is_fresh = age_days <= self.max_age_days
            is_valid = True  # 时间戳格式有效
            
            # 检查是否为未来时间（异常）
            if parsed_date > now + timedelta(days=1):
                is_valid = False
                reason = "future_timestamp"
            else:
                reason = "valid" if is_fresh else "outdated"
            
            return {
                "is_valid": is_valid,
                "is_fresh": is_fresh,
                "age_days": age_days,
                "timestamp": parsed_date.isoformat(),
                "reason": reason,
            }
            
        except Exception as e:
            logger.warning(f"时间戳解析失败: {e}")
            return {
                "is_valid": True,  # 解析失败时不拒绝
                "is_fresh": None,
                "age_days": None,
                "reason": f"parse_error: {str(e)}",
            }


class SourceReliabilityChecker:
    """
    信息来源可靠性检查器
    验证信息来源的可信度
    """

    def __init__(self):
        # 可信域名列表（可以根据需要扩展）
        self.trusted_domains = {
            # 学术和教育
            ".edu", ".ac.", ".gov",
            # 知名新闻媒体（示例）
            "bbc.com", "reuters.com", "ap.org",
            # 其他可信源（可根据需要添加）
        }

        # 可疑域名模式
        self.suspicious_patterns = [
            r"bit\.ly",
            r"tinyurl\.com",
            r"short\.link",
            r"redirect",
        ]

    def check_source(self, source: Optional[str]) -> Dict[str, Any]:
        """
        检查信息来源可靠性
        
        Args:
            source: 信息来源（URL、路径等）
            
        Returns:
            包含可靠性评分的字典
        """
        if not source:
            return {
                "reliability_score": 0.5,  # 未知来源，中等可信度
                "is_trusted": False,
                "reason": "no_source_provided",
            }

        # 检查URL
        if source.startswith(("http://", "https://")):
            try:
                parsed = urlparse(source)
                domain = parsed.netloc.lower()

                # 检查可信域名
                for trusted in self.trusted_domains:
                    if trusted in domain:
                        return {
                            "reliability_score": 0.85,
                            "is_trusted": True,
                            "reason": "trusted_domain",
                            "domain": domain,
                        }

                # 检查可疑模式
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, domain):
                        return {
                            "reliability_score": 0.3,
                            "is_trusted": False,
                            "reason": "suspicious_pattern",
                            "domain": domain,
                        }

                # 默认评分（基于URL结构）
                score = 0.6
                if domain and "." in domain:
                    score = 0.65  # 有效域名

                return {
                    "reliability_score": score,
                    "is_trusted": False,
                    "reason": "standard_url",
                    "domain": domain,
                }
            except Exception as e:
                logger.warning(f"Failed to parse URL {source}: {e}")

        # 检查本地文件路径
        if source.startswith("/") or ":" in source:
            return {
                "reliability_score": 0.7,  # 本地文件中等可信度
                "is_trusted": True,
                "reason": "local_file",
                "path": source,
            }

        # 其他情况
        return {
            "reliability_score": 0.5,
            "is_trusted": False,
            "reason": "unknown_source_type",
        }


class ContentConsistencyChecker:
    """
    内容一致性检查器
    检查内容内部和跨文档的一致性
    """

    def __init__(self):
        # 常见矛盾模式
        self.contradiction_patterns = [
            (r"从不", r"总是"),
            (r"没有", r"有"),
            (r"不能", r"能"),
            (r"错误", r"正确"),
        ]

    def check_consistency(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检查内容一致性
        
        Args:
            text: 要检查的文本
            context: 上下文信息（可包含相关文档）
            
        Returns:
            一致性检查结果
        """
        issues = []
        score = 1.0

        # 检查文本内部矛盾
        text_lower = text.lower()
        for pattern1, pattern2 in self.contradiction_patterns:
            if re.search(pattern1, text_lower) and re.search(pattern2, text_lower):
                issues.append(
                    f"发现内部矛盾: '{pattern1}' 和 '{pattern2}' 同时出现"
                )
                score -= 0.2

        # 检查事实性声明（简单模式匹配）
        fact_patterns = [
            r"(\d{4})年.*(\d{4})年",  # 年份矛盾
            r"(\d+)%.*(\d+)%",  # 百分比矛盾
        ]

        for pattern in fact_patterns:
            matches = re.findall(pattern, text)
            if len(set(matches)) > 1:
                issues.append(f"发现数据不一致: {matches}")
                score -= 0.15

        # 检查重复内容（可能是错误复制）
        sentences = text.split("。")
        if len(sentences) > 2:
            unique_sentences = set(sentences)
            if len(unique_sentences) < len(sentences) * 0.5:
                issues.append("发现大量重复内容")
                score -= 0.1

        return {
            "consistency_score": max(0.0, score),
            "is_consistent": score >= 0.7,
            "issues": issues,
            "issue_count": len(issues),
        }

    def check_cross_document_consistency(
        self, new_text: str, existing_texts: List[str]
    ) -> Dict[str, Any]:
        """
        检查跨文档一致性
        
        Args:
            new_text: 新文本
            existing_texts: 已有文本列表
            
        Returns:
            跨文档一致性检查结果
        """
        if not existing_texts:
            return {
                "consistency_score": 1.0,
                "is_consistent": True,
                "conflicts": [],
            }

        conflicts = []
        score = 1.0

        # 简单的关键词提取和比较
        new_keywords = set(re.findall(r"\w+", new_text.lower()))
        
        for existing_text in existing_texts[:5]:  # 限制比较数量
            existing_keywords = set(re.findall(r"\w+", existing_text.lower()))
            
            # 检查关键信息冲突（简单实现）
            common_keywords = new_keywords & existing_keywords
            if len(common_keywords) > 5:
                # 提取共同关键词周围的上下文进行比较
                # 这里使用简化版本
                if len(new_keywords) > 0 and len(existing_keywords) > 0:
                    similarity = len(common_keywords) / max(
                        len(new_keywords), len(existing_keywords)
                    )
                    if similarity > 0.8:
                        # 可能是重复内容
                        conflicts.append({
                            "type": "possible_duplicate",
                            "similarity": similarity,
                        })
                        score -= 0.1

        return {
            "consistency_score": max(0.0, score),
            "is_consistent": score >= 0.6,
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
        }


class CredibilityScorer:
    """
    可信度评分器
    综合多个因素计算内容可信度
    """

    def __init__(self, max_age_days: int = 365):
        """
        初始化可信度评分器
        
        Args:
            max_age_days: 信息最大有效期（天数）
        """
        self.source_checker = SourceReliabilityChecker()
        self.consistency_checker = ContentConsistencyChecker()
        self.timestamp_validator = TimestampValidator(max_age_days=max_age_days)

    def calculate_credibility(
        self,
        text: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        existing_texts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        计算内容可信度
        
        Args:
            text: 文本内容
            source: 信息来源
            metadata: 元数据
            existing_texts: 已有文本（用于跨文档一致性检查）
            
        Returns:
            可信度评分结果
        """
        # 1. 来源可靠性检查
        source_result = self.source_checker.check_source(source)
        source_score = source_result["reliability_score"]

        # 2. 内容一致性检查
        consistency_result = self.consistency_checker.check_consistency(
            text, metadata
        )
        consistency_score = consistency_result["consistency_score"]

        # 3. 跨文档一致性检查
        cross_consistency_score = 1.0
        if existing_texts:
            cross_result = self.consistency_checker.check_cross_document_consistency(
                text, existing_texts
            )
            cross_consistency_score = cross_result["consistency_score"]

        # 4. 内容质量检查
        quality_score = self._calculate_quality_score(text, metadata)
        
        # 5. 时间戳验证
        timestamp = None
        if metadata:
            timestamp = (
                metadata.get("timestamp") or 
                metadata.get("date") or 
                metadata.get("published_date")
            )
        timestamp_result = self.timestamp_validator.validate_timestamp(
            timestamp, metadata
        )
        timestamp_score = 1.0
        max_age_days = self.timestamp_validator.max_age_days
        if timestamp_result.get("is_fresh") is False:
            # 信息过期，降低可信度
            timestamp_score = max(0.3, 1.0 - (timestamp_result.get("age_days", 0) / (max_age_days * 2)))
        elif timestamp_result.get("is_valid") is False:
            # 时间戳无效（如未来时间）
            timestamp_score = 0.5

        # 6. 综合可信度评分（加权平均）
        weights = {
            "source": 0.25,
            "consistency": 0.2,
            "cross_consistency": 0.2,
            "quality": 0.15,
            "timestamp": 0.2,
        }

        final_score = (
            source_score * weights["source"]
            + consistency_score * weights["consistency"]
            + cross_consistency_score * weights["cross_consistency"]
            + quality_score * weights["quality"]
            + timestamp_score * weights["timestamp"]
        )

        # 确定是否可信
        is_credible = final_score >= 0.65

        return {
            "credibility_score": round(final_score, 3),
            "is_credible": is_credible,
            "component_scores": {
                "source": round(source_score, 3),
                "consistency": round(consistency_score, 3),
                "cross_consistency": round(cross_consistency_score, 3),
                "quality": round(quality_score, 3),
                "timestamp": round(timestamp_score, 3),
            },
            "source_info": source_result,
            "consistency_info": consistency_result,
            "timestamp_info": timestamp_result,
            "recommendation": "accept" if is_credible else "review",
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_quality_score(
        self, text: str, metadata: Optional[Dict[str, Any]]
    ) -> float:
        """
        计算内容质量评分
        
        Args:
            text: 文本内容
            metadata: 元数据
            
        Returns:
            质量评分 (0-1)
        """
        score = 1.0

        # 长度检查
        if len(text) < 10:
            score -= 0.3
        elif len(text) > 50000:
            score -= 0.1  # 过长可能有问题

        # 字符多样性
        unique_chars = len(set(text))
        if len(text) > 0:
            diversity = unique_chars / min(len(text), 1000)
            if diversity < 0.1:
                score -= 0.2  # 字符多样性太低

        # 检查明显错误
        error_patterns = [
            r"测试.*测试.*测试",  # 重复测试内容
            r"临时.*临时",  # 临时内容
            r"TODO|FIXME|XXX",  # 开发标记
        ]

        for pattern in error_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score -= 0.15

        # 元数据质量
        if metadata:
            if metadata.get("quality", {}).get("ok", True):
                score += 0.05  # 质量检查通过
            else:
                score -= 0.1  # 质量检查未通过

        return max(0.0, min(1.0, score))


class AIFactChecker:
    """
    AI辅助事实核查器
    使用LLM进行事实核查和验证
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "qwen2.5:7b"
    
    async def check_facts(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用AI进行事实核查
        
        Args:
            text: 要核查的文本
            context: 上下文信息
            
        Returns:
            事实核查结果
        """
        try:
            import httpx
            
            # 构建提示词
            prompt = f"""请对以下文本进行事实核查，评估其真实性和可信度：

文本内容：
{text[:1000]}

请从以下维度进行评估：
1. 事实准确性（是否有明显错误）
2. 逻辑一致性（是否有矛盾）
3. 信息来源可信度
4. 内容完整性

请以JSON格式返回：
{{
    "factual_accuracy": 0.0-1.0,
    "logical_consistency": 0.0-1.0,
    "source_reliability": 0.0-1.0,
    "content_completeness": 0.0-1.0,
    "overall_score": 0.0-1.0,
    "issues": ["问题列表"],
    "verdict": "可信/可疑/不可信"
}}"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("response", "")
                    
                    # 尝试解析JSON
                    import json
                    import re
                    json_match = re.search(r'\{[^{}]*\}', generated_text, re.DOTALL)
                    if json_match:
                        try:
                            ai_result = json.loads(json_match.group())
                            return {
                                "success": True,
                                "ai_score": ai_result.get("overall_score", 0.5),
                                "factual_accuracy": ai_result.get("factual_accuracy", 0.5),
                                "logical_consistency": ai_result.get("logical_consistency", 0.5),
                                "source_reliability": ai_result.get("source_reliability", 0.5),
                                "content_completeness": ai_result.get("content_completeness", 0.5),
                                "issues": ai_result.get("issues", []),
                                "verdict": ai_result.get("verdict", "未知"),
                                "raw_response": generated_text
                            }
                        except json.JSONDecodeError:
                            pass
                    
                    # 如果JSON解析失败，返回默认值
                    return {
                        "success": True,
                        "ai_score": 0.7,
                        "factual_accuracy": 0.7,
                        "logical_consistency": 0.7,
                        "source_reliability": 0.7,
                        "content_completeness": 0.7,
                        "issues": [],
                        "verdict": "需要人工审核",
                        "raw_response": generated_text
                    }
                else:
                    return {
                        "success": False,
                        "error": f"AI服务调用失败: {response.status_code}",
                        "ai_score": 0.5
                    }
        except Exception as e:
            logger.warning(f"AI事实核查失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "ai_score": 0.5
            }


class ExternalFactChecker:
    """
    外部事实核查器
    通过网络搜索验证事实
    """
    
    def __init__(self):
        self.search_engines = ["google", "bing", "duckduckgo"]
    
    async def verify_with_search(
        self,
        claim: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        通过网络搜索验证声明
        
        Args:
            claim: 要验证的声明
            max_results: 最大搜索结果数
            
        Returns:
            验证结果
        """
        try:
            import httpx
            
            # 提取关键信息
            keywords = self._extract_keywords(claim)
            search_query = " ".join(keywords[:5])
            
            # 调用搜索服务（假设有搜索API）
            search_url = "http://localhost:8015/api/search"  # 趋势分析系统的搜索API
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get(
                        search_url,
                        params={"query": search_query, "limit": max_results}
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        search_results = results.get("results", [])
                        
                        # 分析搜索结果与声明的相关性
                        relevance_score = self._calculate_relevance(claim, search_results)
                        
                        return {
                            "success": True,
                            "relevance_score": relevance_score,
                            "search_results_count": len(search_results),
                            "verification_status": "verified" if relevance_score > 0.7 else "unverified",
                            "search_results": search_results[:3]  # 只返回前3个结果
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"搜索服务不可用: {response.status_code}",
                            "relevance_score": 0.5
                        }
                except httpx.ConnectError:
                    # 搜索服务不可用，返回默认值
                    return {
                        "success": False,
                        "error": "搜索服务不可用",
                        "relevance_score": 0.5
                    }
        except Exception as e:
            logger.warning(f"外部事实核查失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "relevance_score": 0.5
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re
        # 简单的关键词提取（可以改进）
        words = re.findall(r'\b\w+\b', text.lower())
        # 过滤停用词
        stop_words = {"的", "是", "在", "有", "和", "与", "或", "the", "is", "a", "an", "and", "or"}
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:10]
    
    def _calculate_relevance(self, claim: str, search_results: List[Dict]) -> float:
        """计算搜索结果与声明的相关性"""
        if not search_results:
            return 0.0
        
        claim_keywords = set(self._extract_keywords(claim))
        total_relevance = 0.0
        
        for result in search_results[:5]:
            result_text = result.get("title", "") + " " + result.get("snippet", "")
            result_keywords = set(self._extract_keywords(result_text))
            
            # 计算关键词重叠度
            if claim_keywords:
                overlap = len(claim_keywords & result_keywords) / len(claim_keywords)
                total_relevance += overlap
        
        return min(1.0, total_relevance / len(search_results[:5]))


class VerificationReportGenerator:
    """
    验证报告生成器
    生成详细的验证报告和可视化
    """
    
    def generate_report(
        self,
        verification_result: Dict[str, Any],
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        生成验证报告
        
        Args:
            verification_result: 验证结果
            include_details: 是否包含详细信息
            
        Returns:
            验证报告
        """
        credibility = verification_result.get("credibility", {})
        component_scores = credibility.get("component_scores", {})
        
        report = {
            "summary": {
                "verified": verification_result.get("verified", False),
                "overall_score": credibility.get("credibility_score", 0.0),
                "recommendation": credibility.get("recommendation", "review"),
                "timestamp": verification_result.get("timestamp", "")
            },
            "component_scores": component_scores,
            "breakdown": {
                "source_reliability": {
                    "score": component_scores.get("source", 0.0),
                    "status": self._get_status(component_scores.get("source", 0.0)),
                    "description": self._get_source_description(component_scores.get("source", 0.0))
                },
                "content_consistency": {
                    "score": component_scores.get("consistency", 0.0),
                    "status": self._get_status(component_scores.get("consistency", 0.0)),
                    "description": self._get_consistency_description(component_scores.get("consistency", 0.0))
                },
                "cross_document_consistency": {
                    "score": component_scores.get("cross_consistency", 0.0),
                    "status": self._get_status(component_scores.get("cross_consistency", 0.0)),
                    "description": "跨文档一致性检查"
                },
                "content_quality": {
                    "score": component_scores.get("quality", 0.0),
                    "status": self._get_status(component_scores.get("quality", 0.0)),
                    "description": "内容质量评估"
                },
                "timestamp_validity": {
                    "score": component_scores.get("timestamp", 0.0),
                    "status": self._get_status(component_scores.get("timestamp", 0.0)),
                    "description": "时间戳有效性检查"
                }
            }
        }
        
        if include_details:
            report["details"] = {
                "source_info": credibility.get("source_info", {}),
                "consistency_info": credibility.get("consistency_info", {}),
                "timestamp_info": credibility.get("timestamp_info", {})
            }
        
        # 生成建议
        report["recommendations"] = self._generate_recommendations(component_scores)
        
        return report
    
    def _get_status(self, score: float) -> str:
        """获取状态"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.65:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "poor"
    
    def _get_source_description(self, score: float) -> str:
        """获取来源描述"""
        if score >= 0.8:
            return "来源高度可信"
        elif score >= 0.65:
            return "来源基本可信"
        elif score >= 0.5:
            return "来源可信度一般"
        else:
            return "来源可信度较低"
    
    def _get_consistency_description(self, score: float) -> str:
        """获取一致性描述"""
        if score >= 0.8:
            return "内容高度一致"
        elif score >= 0.65:
            return "内容基本一致"
        elif score >= 0.5:
            return "存在一些不一致"
        else:
            return "存在明显矛盾"
    
    def _generate_recommendations(self, component_scores: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if component_scores.get("source", 1.0) < 0.65:
            recommendations.append("建议验证信息来源的可信度")
        
        if component_scores.get("consistency", 1.0) < 0.65:
            recommendations.append("建议检查内容内部一致性")
        
        if component_scores.get("quality", 1.0) < 0.65:
            recommendations.append("建议提高内容质量")
        
        if component_scores.get("timestamp", 1.0) < 0.65:
            recommendations.append("建议更新过时信息")
        
        if not recommendations:
            recommendations.append("内容验证通过，可以入库")
        
        return recommendations


class EnhancedTruthVerification:
    """
    增强的真实性验证器
    集成所有验证功能，提供统一的验证接口
    """

    def __init__(self, enable_ai_check: bool = True, enable_external_check: bool = False):
        self.scorer = CredibilityScorer()
        self.consistency_checker = ContentConsistencyChecker()
        self.source_checker = SourceReliabilityChecker()
        self.ai_checker = AIFactChecker() if enable_ai_check else None
        self.external_checker = ExternalFactChecker() if enable_external_check else None
        self.report_generator = VerificationReportGenerator()
        self.verification_history = []  # 验证历史记录

    async def verify_content(
        self,
        text: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        existing_texts: Optional[List[str]] = None,
        min_credibility: float = 0.65,
        use_ai_check: bool = False,
        use_external_check: bool = False,
    ) -> Dict[str, Any]:
        """
        验证内容真实性（深化版）
        
        Args:
            text: 要验证的文本内容
            source: 信息来源
            metadata: 元数据
            existing_texts: 已有文本（用于一致性检查）
            min_credibility: 最低可信度阈值
            use_ai_check: 是否使用AI辅助验证
            use_external_check: 是否使用外部搜索验证
            
        Returns:
            验证结果字典
        """
        # 1. 基础可信度计算
        credibility_result = self.scorer.calculate_credibility(
            text=text,
            source=source,
            metadata=metadata,
            existing_texts=existing_texts,
        )
        
        base_score = credibility_result["credibility_score"]
        
        # 2. AI辅助验证（可选）
        ai_score = None
        ai_result = None
        if use_ai_check and self.ai_checker:
            try:
                ai_result = await self.ai_checker.check_facts(text, metadata)
                if ai_result.get("success"):
                    ai_score = ai_result.get("ai_score", 0.5)
                    # 将AI评分纳入综合评分（权重30%）
                    base_score = base_score * 0.7 + ai_score * 0.3
            except Exception as e:
                logger.warning(f"AI验证失败: {e}")
        
        # 3. 外部搜索验证（可选）
        external_score = None
        external_result = None
        if use_external_check and self.external_checker:
            try:
                external_result = await self.external_checker.verify_with_search(text)
                if external_result.get("success"):
                    external_score = external_result.get("relevance_score", 0.5)
                    # 将外部验证评分纳入综合评分（权重20%）
                    base_score = base_score * 0.8 + external_score * 0.2
            except Exception as e:
                logger.warning(f"外部验证失败: {e}")
        
        # 更新可信度评分
        credibility_result["credibility_score"] = round(base_score, 3)
        credibility_result["ai_verification"] = ai_result
        credibility_result["external_verification"] = external_result
        
        # 决定是否接受
        is_acceptable = base_score >= min_credibility
        
        # 生成详细报告
        verification_result = {
            "verified": is_acceptable,
            "credibility": credibility_result,
            "action": "accept" if is_acceptable else "reject",
            "reason": (
                "可信度达标"
                if is_acceptable
                else f"可信度低于阈值 {min_credibility}"
            ),
            "timestamp": datetime.now().isoformat(),
            "verification_methods": {
                "base_credibility": True,
                "ai_check": use_ai_check and ai_result is not None,
                "external_check": use_external_check and external_result is not None
            }
        }
        
        # 生成详细报告
        verification_result["report"] = self.report_generator.generate_report(
            verification_result,
            include_details=True
        )
        
        # 记录验证历史
        self.verification_history.append({
            "timestamp": datetime.now().isoformat(),
            "text_preview": text[:100],
            "source": source,
            "score": base_score,
            "verified": is_acceptable,
            "methods": verification_result["verification_methods"]
        })
        
        # 限制历史记录数量（保留最近1000条）
        if len(self.verification_history) > 1000:
            self.verification_history = self.verification_history[-1000:]
        
        return verification_result

    async def filter_content(
        self,
        content_list: List[Dict[str, Any]],
        min_credibility: float = 0.65,
        use_ai_check: bool = False,
        use_external_check: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        过滤内容列表，移除低可信度内容（异步版）
        
        Args:
            content_list: 内容列表，每个元素包含 text, source, metadata
            min_credibility: 最低可信度阈值
            use_ai_check: 是否使用AI验证
            use_external_check: 是否使用外部验证
            
        Returns:
            (accepted_list, rejected_list) 元组
        """
        accepted = []
        rejected = []

        for content in content_list:
            text = content.get("text", "")
            source = content.get("source")
            metadata = content.get("metadata", {})

            result = await self.verify_content(
                text=text,
                source=source,
                metadata=metadata,
                min_credibility=min_credibility,
                use_ai_check=use_ai_check,
                use_external_check=use_external_check,
            )

            if result["verified"]:
                # 添加验证信息到元数据
                content["verification"] = result["credibility"]
                accepted.append(content)
            else:
                content["verification"] = result["credibility"]
                content["rejection_reason"] = result["reason"]
                rejected.append(content)

        return accepted, rejected
    
    async def batch_verify(
        self,
        content_list: List[Dict[str, Any]],
        min_credibility: float = 0.65,
        use_ai_check: bool = False,
        use_external_check: bool = False,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        批量验证内容（优化版）
        
        Args:
            content_list: 内容列表
            min_credibility: 最低可信度阈值
            use_ai_check: 是否使用AI验证
            use_external_check: 是否使用外部验证
            max_concurrent: 最大并发数
            
        Returns:
            批量验证结果
        """
        import asyncio
        
        accepted = []
        rejected = []
        verification_stats = {
            "total": len(content_list),
            "accepted": 0,
            "rejected": 0,
            "average_score": 0.0,
            "scores_distribution": {
                "excellent": 0,  # >= 0.8
                "good": 0,       # 0.65-0.8
                "fair": 0,       # 0.5-0.65
                "poor": 0        # < 0.5
            }
        }
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def verify_one(content: Dict[str, Any]):
            async with semaphore:
                text = content.get("text", "")
                source = content.get("source")
                metadata = content.get("metadata", {})
                
                result = await self.verify_content(
                    text=text,
                    source=source,
                    metadata=metadata,
                    min_credibility=min_credibility,
                    use_ai_check=use_ai_check,
                    use_external_check=use_external_check,
                )
                
                return content, result
        
        # 并发执行验证
        tasks = [verify_one(content) for content in content_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        total_score = 0.0
        for item in results:
            if isinstance(item, Exception):
                logger.error(f"批量验证出错: {item}")
                continue
            
            content, result = item
            
            score = result["credibility"]["credibility_score"]
            total_score += score
            
            # 统计分布
            if score >= 0.8:
                verification_stats["scores_distribution"]["excellent"] += 1
            elif score >= 0.65:
                verification_stats["scores_distribution"]["good"] += 1
            elif score >= 0.5:
                verification_stats["scores_distribution"]["fair"] += 1
            else:
                verification_stats["scores_distribution"]["poor"] += 1
            
            if result["verified"]:
                content["verification"] = result["credibility"]
                accepted.append(content)
                verification_stats["accepted"] += 1
            else:
                content["verification"] = result["credibility"]
                content["rejection_reason"] = result["reason"]
                rejected.append(content)
                verification_stats["rejected"] += 1
        
        # 计算平均分
        if len(content_list) > 0:
            verification_stats["average_score"] = round(total_score / len(content_list), 3)
        
        return {
            "accepted": accepted,
            "rejected": rejected,
            "stats": verification_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        获取验证统计信息
        
        Returns:
            统计信息
        """
        if not self.verification_history:
            return {
                "total_verifications": 0,
                "average_score": 0.0,
                "acceptance_rate": 0.0
            }
        
        total = len(self.verification_history)
        total_score = sum(h["score"] for h in self.verification_history)
        accepted_count = sum(1 for h in self.verification_history if h["verified"])
        
        return {
            "total_verifications": total,
            "average_score": round(total_score / total, 3) if total > 0 else 0.0,
            "acceptance_rate": round(accepted_count / total, 3) if total > 0 else 0.0,
            "recent_verifications": self.verification_history[-10:]  # 最近10条
        }


# 全局实例（单例模式）
_verification_instance: Optional[EnhancedTruthVerification] = None


def get_truth_verifier() -> EnhancedTruthVerification:
    """
    获取真实性验证器实例（单例）
    
    Returns:
        EnhancedTruthVerification实例
    """
    global _verification_instance
    if _verification_instance is None:
        _verification_instance = EnhancedTruthVerification()
    return _verification_instance

