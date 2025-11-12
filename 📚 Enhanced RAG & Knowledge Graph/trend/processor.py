"""信息处理器"""
import logging
from typing import List
from .models import TrendData, Analysis

logger = logging.getLogger(__name__)

class TrendProcessor:
    def __init__(self):
        logger.info("✅ 信息处理器已初始化")
    
    def process_data(self, data_list: List[TrendData]) -> Analysis:
        """处理信息"""
        if not data_list:
            raise ValueError("无数据可处理")
        
        # 汇总分析
        topics = set()
        for data in data_list:
            topics.add(data.category)
        
        summary = f"共分析{len(data_list)}条数据，涉及{len(topics)}个主题"
        
        key_points = [data.title for data in data_list[:5]]  # 前5条作为要点
        
        analysis = Analysis(
            tenant_id=data_list[0].tenant_id,
            topic=", ".join(topics),
            summary=summary,
            key_points=key_points,
            sentiment="neutral"
        )
        
        logger.info(f"信息已处理: {summary}")
        return analysis
    
    def classify_data(self, data_list: List[TrendData]) -> dict:
        """分类数据"""
        by_category = {}
        for data in data_list:
            cat = data.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(data)
        return by_category

trend_processor = TrendProcessor()












