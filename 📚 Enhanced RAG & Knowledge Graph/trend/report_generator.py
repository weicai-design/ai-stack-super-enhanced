"""报告生成器"""
import logging
from .models import Report, Analysis

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        logger.info("✅ 报告生成器已初始化")
    
    def generate_report(
        self,
        tenant_id: str,
        analysis: Analysis,
        report_type: str = "industry"
    ) -> Report:
        """生成报告"""
        content = f"""
# {report_type.upper()}分析报告

## 概要
{analysis.summary}

## 关键要点
"""
        for i, point in enumerate(analysis.key_points, 1):
            content += f"{i}. {point}\n"
        
        content += f"\n## 总体情绪\n{analysis.sentiment}"
        
        report = Report(
            tenant_id=tenant_id,
            title=f"{report_type}分析报告",
            content=content,
            report_type=report_type
        )
        
        logger.info(f"报告已生成: {report.title}")
        return report

report_generator = ReportGenerator()






















