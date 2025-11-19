#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势分析 RAG 输出
功能：将趋势分析结果输出到RAG系统，支持知识图谱关联
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TrendRAGOutput:
    """
    趋势分析 RAG 输出器
    将趋势分析结果写入RAG系统
    """
    
    def __init__(self):
        """初始化RAG输出器"""
        self.output_logs: List[Dict[str, Any]] = []
        self.rag_connections: Dict[str, List[str]] = defaultdict(list)  # 指标 -> RAG文档ID列表
    
    def generate_rag_document(
        self,
        indicator: str,
        analysis_result: Dict[str, Any],
        document_type: str = "trend_analysis"
    ) -> Dict[str, Any]:
        """
        生成RAG文档
        
        Args:
            indicator: 指标名称
            analysis_result: 分析结果
            document_type: 文档类型
            
        Returns:
            RAG文档
        """
        # 构建文档内容
        content_parts = []
        
        # 1. 指标基本信息
        content_parts.append(f"# {indicator} 趋势分析报告")
        content_parts.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 2. 分析摘要
        if "summary" in analysis_result:
            content_parts.append(f"\n## 分析摘要\n{analysis_result['summary']}")
        
        # 3. 关键指标
        if "metrics" in analysis_result:
            metrics = analysis_result["metrics"]
            content_parts.append("\n## 关键指标")
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    content_parts.append(f"- {key}: {value:.2f}")
                else:
                    content_parts.append(f"- {key}: {value}")
        
        # 4. 趋势预测
        if "prediction" in analysis_result:
            pred = analysis_result["prediction"]
            content_parts.append("\n## 趋势预测")
            if isinstance(pred, dict):
                for key, value in pred.items():
                    content_parts.append(f"- {key}: {value}")
            else:
                content_parts.append(f"- 预测: {pred}")
        
        # 5. 建议与洞察
        if "recommendations" in analysis_result:
            content_parts.append("\n## 建议与洞察")
            for rec in analysis_result["recommendations"]:
                content_parts.append(f"- {rec}")
        
        # 6. 数据来源
        if "sources" in analysis_result:
            content_parts.append("\n## 数据来源")
            for source in analysis_result["sources"]:
                content_parts.append(f"- {source}")
        
        # 合并内容
        content = "\n".join(content_parts)
        
        # 提取关键词和标签
        keywords = self._extract_keywords(indicator, analysis_result)
        tags = [indicator, document_type, "trend_analysis"]
        
        # 构建RAG文档
        rag_document = {
            "title": f"{indicator} 趋势分析",
            "content": content,
            "metadata": {
                "indicator": indicator,
                "document_type": document_type,
                "generated_at": datetime.now().isoformat(),
                "keywords": keywords,
                "tags": tags,
                "source": "trend_analysis",
            },
            "embeddings_ready": True,  # 标记为可嵌入
        }
        
        return rag_document
    
    def _extract_keywords(
        self,
        indicator: str,
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """提取关键词"""
        keywords = [indicator]
        
        # 从指标名称提取
        if "_" in indicator:
            keywords.extend(indicator.split("_"))
        
        # 从分析结果提取
        if "factors" in analysis_result:
            for factor in analysis_result["factors"]:
                if isinstance(factor, str):
                    keywords.append(factor)
        
        # 去重并返回
        return list(set(keywords))
    
    def record_rag_output(
        self,
        indicator: str,
        rag_document_id: str,
        status: str = "success",
        error: Optional[str] = None
    ):
        """
        记录RAG输出
        
        Args:
            indicator: 指标名称
            rag_document_id: RAG文档ID
            status: 状态
            error: 错误信息
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "indicator": indicator,
            "rag_document_id": rag_document_id,
            "status": status,
            "error": error,
        }
        
        self.output_logs.append(log_entry)
        self.output_logs = self.output_logs[-500:]  # 保留最近500条
        
        # 记录关联
        if status == "success":
            self.rag_connections[indicator].append(rag_document_id)
    
    def get_rag_connections(
        self,
        indicator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取RAG关联信息
        
        Args:
            indicator: 指标名称（None表示全部）
            
        Returns:
            RAG关联信息
        """
        if indicator:
            return {
                "indicator": indicator,
                "rag_documents": self.rag_connections.get(indicator, []),
                "count": len(self.rag_connections.get(indicator, [])),
            }
        
        return {
            "total_indicators": len(self.rag_connections),
            "total_documents": sum(len(docs) for docs in self.rag_connections.values()),
            "connections": {
                ind: {
                    "rag_documents": docs,
                    "count": len(docs)
                }
                for ind, docs in self.rag_connections.items()
            }
        }
    
    def get_output_stats(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取输出统计
        
        Args:
            days: 时间范围（天）
            
        Returns:
            输出统计
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        logs = [
            log for log in self.output_logs
            if datetime.fromisoformat(log["timestamp"]) >= cutoff
        ]
        
        success_count = len([log for log in logs if log["status"] == "success"])
        error_count = len([log for log in logs if log["status"] == "error"])
        
        # 按指标统计
        indicator_stats = defaultdict(lambda: {"success": 0, "error": 0})
        for log in logs:
            ind = log["indicator"]
            if log["status"] == "success":
                indicator_stats[ind]["success"] += 1
            else:
                indicator_stats[ind]["error"] += 1
        
        return {
            "period": {
                "days": days,
                "start": cutoff.isoformat(),
                "end": datetime.now().isoformat()
            },
            "total_outputs": len(logs),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round(success_count / len(logs) * 100, 2) if logs else 0.0,
            "indicator_stats": dict(indicator_stats),
        }


# 全局实例
trend_rag_output = TrendRAGOutput()

