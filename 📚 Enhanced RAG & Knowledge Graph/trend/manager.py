"""
趋势管理器（增强版）
Trend Manager

版本: v1.0.0
"""

import logging
from typing import Dict, List
from collections import defaultdict
from .models import TrendData, Report, Analysis
from .crawler import trend_crawler
from .processor import trend_processor
from .report_generator import report_generator

logger = logging.getLogger(__name__)


class TrendManager:
    """趋势管理器（增强版）"""
    
    def __init__(self):
        self.data: Dict[str, List[TrendData]] = defaultdict(list)
        self.analyses: Dict[str, List[Analysis]] = defaultdict(list)
        self.reports: Dict[str, List[Report]] = defaultdict(list)
        
        # 核心组件
        self.crawler = trend_crawler
        self.processor = trend_processor
        self.report_gen = report_generator
        
        logger.info("✅ 趋势管理器（增强版）已初始化")
    
    # ==================== 数据采集 ====================
    
    def collect_data(self, tenant_id: str, data: TrendData) -> TrendData:
        """收集数据"""
        data.tenant_id = tenant_id
        self.data[tenant_id].append(data)
        return data
    
    def crawl_news(self, tenant_id: str, category: str, keywords: List[str]) -> List[TrendData]:
        """爬取新闻"""
        data_list = self.crawler.crawl_news(category, keywords)
        for data in data_list:
            data.tenant_id = tenant_id
            self.data[tenant_id].append(data)
        return data_list
    
    def get_data(self, tenant_id: str, category: str = None) -> List[TrendData]:
        """获取数据"""
        data = self.data.get(tenant_id, [])
        if category:
            data = [d for d in data if d.category == category]
        return data
    
    # ==================== 分析处理 ====================
    
    def create_analysis(self, tenant_id: str, analysis: Analysis) -> Analysis:
        """创建分析"""
        analysis.tenant_id = tenant_id
        self.analyses[tenant_id].append(analysis)
        return analysis
    
    def process_and_analyze(self, tenant_id: str, category: str = None) -> Analysis:
        """处理和分析数据"""
        data_list = self.get_data(tenant_id, category)
        analysis = self.processor.process_data(data_list)
        analysis.tenant_id = tenant_id
        self.analyses[tenant_id].append(analysis)
        return analysis
    
    def get_analyses(self, tenant_id: str) -> List[Analysis]:
        """获取分析列表"""
        return self.analyses.get(tenant_id, [])
    
    # ==================== 报告生成 ====================
    
    def generate_report(self, tenant_id: str, report: Report) -> Report:
        """生成报告"""
        report.tenant_id = tenant_id
        self.reports[tenant_id].append(report)
        return report
    
    def generate_from_analysis(
        self,
        tenant_id: str,
        analysis_id: str,
        report_type: str
    ) -> Report:
        """基于分析生成报告"""
        # 找到分析
        analysis = None
        for a in self.analyses.get(tenant_id, []):
            if a.id == analysis_id:
                analysis = a
                break
        
        if not analysis:
            raise ValueError("分析不存在")
        
        report = self.report_gen.generate_report(tenant_id, analysis, report_type)
        self.reports[tenant_id].append(report)
        return report
    
    def get_reports(self, tenant_id: str) -> List[Report]:
        """获取报告列表"""
        return self.reports.get(tenant_id, [])


trend_manager = TrendManager()

