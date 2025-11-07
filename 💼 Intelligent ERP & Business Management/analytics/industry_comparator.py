"""
行业对比分析器
实现与同行业企业的数据对比和分析
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics


class IndustryComparator:
    """行业对比分析器"""
    
    def __init__(self):
        """初始化对比分析器"""
        self.industry_data_sources = {}
        self.benchmark_data = {}
        self.comparison_history = []
    
    def register_industry_data_source(
        self,
        source_name: str,
        source_type: str,
        data_provider: callable
    ) -> Dict[str, Any]:
        """
        注册行业数据源
        
        Args:
            source_name: 数据源名称
            source_type: 类型（public_report/industry_association/market_research）
            data_provider: 数据提供函数
        
        Returns:
            注册结果
        """
        self.industry_data_sources[source_name] = {
            "source_name": source_name,
            "source_type": source_type,
            "data_provider": data_provider,
            "registered_at": datetime.now().isoformat(),
            "active": True
        }
        
        return {
            "success": True,
            "message": f"数据源 {source_name} 已注册"
        }
    
    def fetch_industry_benchmarks(
        self,
        industry: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        获取行业基准数据
        
        Args:
            industry: 行业名称
            metrics: 指标列表
        
        Returns:
            基准数据
        """
        benchmarks = {}
        
        # 从各数据源获取数据
        for source_name, source_info in self.industry_data_sources.items():
            if not source_info["active"]:
                continue
            
            try:
                # 调用数据提供函数
                data_provider = source_info["data_provider"]
                source_data = data_provider(industry, metrics)
                
                for metric in metrics:
                    if metric in source_data:
                        if metric not in benchmarks:
                            benchmarks[metric] = []
                        benchmarks[metric].append({
                            "source": source_name,
                            "value": source_data[metric]
                        })
            
            except Exception as e:
                print(f"数据源 {source_name} 获取失败: {str(e)}")
        
        # 计算平均基准值
        industry_benchmarks = {}
        for metric, values in benchmarks.items():
            if values:
                avg_value = statistics.mean([v["value"] for v in values])
                industry_benchmarks[metric] = {
                    "average": avg_value,
                    "sources_count": len(values),
                    "values": values
                }
        
        return {
            "success": True,
            "industry": industry,
            "benchmarks": industry_benchmarks,
            "data_sources_used": len(self.industry_data_sources)
        }
    
    def compare_with_industry(
        self,
        company_data: Dict[str, Any],
        industry: str
    ) -> Dict[str, Any]:
        """
        与行业对比
        
        Args:
            company_data: 公司数据 {
                "revenue_growth": 0.15,
                "profit_margin": 0.12,
                "asset_turnover": 1.5,
                "roe": 0.18
            }
            industry: 行业名称
        
        Returns:
            对比分析
        """
        # 获取行业基准
        metrics = list(company_data.keys())
        benchmarks_result = self.fetch_industry_benchmarks(industry, metrics)
        
        if not benchmarks_result.get("benchmarks"):
            # 如果没有外部数据，使用内置基准
            benchmarks = self._get_builtin_benchmarks(industry, metrics)
        else:
            benchmarks = benchmarks_result["benchmarks"]
        
        # 对比分析
        comparison = {}
        for metric, company_value in company_data.items():
            if metric in benchmarks:
                benchmark = benchmarks[metric]
                benchmark_avg = benchmark.get("average", 0) if isinstance(benchmark, dict) else benchmark
                
                # 计算差异
                difference = company_value - benchmark_avg
                difference_percent = (difference / benchmark_avg * 100) if benchmark_avg != 0 else 0
                
                # 评估
                if difference_percent > 10:
                    performance = "优于行业"
                    grade = "A"
                elif difference_percent > 0:
                    performance = "略优于行业"
                    grade = "B"
                elif difference_percent > -10:
                    performance = "接近行业平均"
                    grade = "C"
                else:
                    performance = "低于行业"
                    grade = "D"
                
                comparison[metric] = {
                    "company_value": company_value,
                    "industry_average": benchmark_avg,
                    "difference": round(difference, 4),
                    "difference_percent": round(difference_percent, 2),
                    "performance": performance,
                    "grade": grade
                }
        
        # 综合评估
        grades = [c["grade"] for c in comparison.values()]
        grade_scores = {"A": 4, "B": 3, "C": 2, "D": 1}
        avg_score = statistics.mean([grade_scores[g] for g in grades])
        
        if avg_score >= 3.5:
            overall_assessment = "行业领先"
        elif avg_score >= 2.5:
            overall_assessment = "行业中上"
        elif avg_score >= 1.5:
            overall_assessment = "行业中等"
        else:
            overall_assessment = "行业落后"
        
        # 保存对比历史
        comparison_record = {
            "timestamp": datetime.now().isoformat(),
            "industry": industry,
            "comparison": comparison,
            "overall_assessment": overall_assessment
        }
        self.comparison_history.append(comparison_record)
        
        return {
            "success": True,
            "industry": industry,
            "comparison": comparison,
            "overall_assessment": overall_assessment,
            "average_score": round(avg_score, 2)
        }
    
    def analyze_competitive_position(
        self,
        company_data: Dict[str, Any],
        competitors_data: List[Dict[str, Any]],
        industry: str
    ) -> Dict[str, Any]:
        """
        分析竞争地位
        
        Args:
            company_data: 公司数据
            competitors_data: 竞争对手数据列表
            industry: 行业
        
        Returns:
            竞争地位分析
        """
        # 计算排名
        all_companies = [company_data] + competitors_data
        
        rankings = {}
        for metric in company_data.keys():
            # 按指标排序
            sorted_companies = sorted(
                all_companies,
                key=lambda x: x.get(metric, 0),
                reverse=True
            )
            
            # 找到公司排名
            company_rank = next(
                (i + 1 for i, c in enumerate(sorted_companies) if c == company_data),
                len(all_companies)
            )
            
            rankings[metric] = {
                "rank": company_rank,
                "total_companies": len(all_companies),
                "percentile": round((1 - company_rank / len(all_companies)) * 100, 2)
            }
        
        # 综合排名
        avg_rank = statistics.mean([r["rank"] for r in rankings.values()])
        
        return {
            "success": True,
            "industry": industry,
            "rankings_by_metric": rankings,
            "average_rank": round(avg_rank, 1),
            "total_competitors": len(competitors_data),
            "competitive_position": self._get_position_label(avg_rank, len(all_companies))
        }
    
    def _get_builtin_benchmarks(
        self,
        industry: str,
        metrics: List[str]
    ) -> Dict[str, float]:
        """
        获取内置基准数据
        
        Args:
            industry: 行业
            metrics: 指标
        
        Returns:
            基准数据
        """
        # 内置的行业基准数据（示例）
        builtin_benchmarks = {
            "制造业": {
                "revenue_growth": 0.08,
                "profit_margin": 0.10,
                "asset_turnover": 1.2,
                "roe": 0.15,
                "current_ratio": 1.5,
                "debt_ratio": 0.5
            },
            "电子": {
                "revenue_growth": 0.12,
                "profit_margin": 0.15,
                "asset_turnover": 1.5,
                "roe": 0.20,
                "current_ratio": 1.8,
                "debt_ratio": 0.45
            },
            "化工": {
                "revenue_growth": 0.06,
                "profit_margin": 0.08,
                "asset_turnover": 1.0,
                "roe": 0.12,
                "current_ratio": 1.4,
                "debt_ratio": 0.55
            }
        }
        
        industry_benchmarks = builtin_benchmarks.get(industry, builtin_benchmarks["制造业"])
        
        return {
            metric: industry_benchmarks.get(metric, 0)
            for metric in metrics
        }
    
    def _get_position_label(self, avg_rank: float, total: int) -> str:
        """
        获取地位标签
        
        Args:
            avg_rank: 平均排名
            total: 总数
        
        Returns:
            地位标签
        """
        percentile = (1 - avg_rank / total) * 100
        
        if percentile >= 90:
            return "行业领导者"
        elif percentile >= 75:
            return "行业领先者"
        elif percentile >= 50:
            return "行业中上游"
        elif percentile >= 25:
            return "行业中等水平"
        else:
            return "行业落后者"


# 创建默认实例
industry_comparator = IndustryComparator()


# 注册示例数据源
def sample_public_data_provider(industry: str, metrics: List[str]) -> Dict[str, float]:
    """
    示例公开数据提供函数
    实际使用时可对接真实数据源API
    """
    # 模拟从公开数据源获取
    return {
        "revenue_growth": 0.10,
        "profit_margin": 0.12,
        "asset_turnover": 1.3,
        "roe": 0.16
    }

# 注册数据源
industry_comparator.register_industry_data_source(
    "公开财报数据",
    "public_report",
    sample_public_data_provider
)





























