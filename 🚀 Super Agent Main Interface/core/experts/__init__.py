"""
AI专家模型系统
包含53个AI专家，覆盖所有模块
"""

from typing import Any, Dict

from .rag_experts import (
    KnowledgeExpert,
    RetrievalExpert,
    GraphExpert,
    get_rag_experts,
)

from .erp_experts import (
    ERPDimension,
    ERPAnalysis,
    ERPDataConnector,
    QualityExpert,
    QualityImprovementExpert,
    CostExpert,
    CostOptimizationExpert,
    DeliveryExpert,
    DeliveryResilienceExpert,
    SafetyExpert,
    SafetyComplianceExpert,
    ProfitExpert,
    ProfitGrowthExpert,
    EfficiencyExpert,
    EfficiencyAutomationExpert,
    ManagementExpert,
    ERPProcessExpert,
    TechnologyExpert,
    TechnologyInnovationExpert,
    ERPExpertCollaboration,
    get_erp_experts,
)

from .content_experts import (
    ContentPlanningExpert,
    ContentGenerationExpert,
    ContentDeAIExpert,
    ContentPublishExpert,
    ContentOperationExpert,
    ContentCopyrightExpert,
    ContentDataConnector,
    ContentExpertCollaboration,
    ContentAnalysis,
    get_content_experts,
)

from .trend_experts import (
    TrendCollectionExpert,
    TrendProcessingExpert,
    TrendAnalysisExpert,
    TrendPredictionExpert,
    TrendReportExpert,
    TrendAlertExpert,
    get_trend_experts,
)

from .stock_experts import (
    StockQuoteExpert,
    StockStrategyExpert,
    StockTradingExpert,
    StockRiskExpert,
    StockBacktestExpert,
    StockPredictionExpert,
    StockPortfolioExpert,
    get_stock_experts,
)

from .operations_finance_experts import (
    OperationsAnalysisExpert,
    UserAnalysisExpert,
    ActivityExpert,
    ChannelExpert,
    FinanceAccountingExpert,
    CostManagementExpert,
    BudgetExpert,
    ReportExpert,
    TaxExpert,
    RiskControlExpert,
    get_operations_finance_experts,
)

from .coding_experts import (
    CodeGenerationExpert,
    CodeReviewExpert,
    PerformanceOptimizationExpert,
    BugFixExpert,
    DocumentationExpert,
    get_coding_experts,
)

from ..expert_collaboration import ExpertCollaborationHub

__all__ = [
    # RAG专家
    "KnowledgeExpert",
    "RetrievalExpert",
    "GraphExpert",
    "get_rag_experts",
    # ERP专家
    "ERPDimension",
    "ERPAnalysis",
    "ERPDataConnector",
    "QualityExpert",
    "QualityImprovementExpert",
    "CostExpert",
    "CostOptimizationExpert",
    "DeliveryExpert",
    "DeliveryResilienceExpert",
    "SafetyExpert",
    "SafetyComplianceExpert",
    "ProfitExpert",
    "ProfitGrowthExpert",
    "EfficiencyExpert",
    "EfficiencyAutomationExpert",
    "ManagementExpert",
    "ERPProcessExpert",
    "TechnologyExpert",
    "TechnologyInnovationExpert",
    "ERPExpertCollaboration",
    "get_erp_experts",
    # 内容专家
    "ContentPlanningExpert",
    "ContentGenerationExpert",
    "ContentDeAIExpert",
    "ContentPublishExpert",
    "ContentOperationExpert",
    "ContentCopyrightExpert",
    "ContentDataConnector",
    "ContentExpertCollaboration",
    "ContentAnalysis",
    "get_content_experts",
    # 趋势专家
    "TrendCollectionExpert",
    "TrendProcessingExpert",
    "TrendAnalysisExpert",
    "TrendPredictionExpert",
    "TrendReportExpert",
    "TrendAlertExpert",
    "get_trend_experts",
    # 股票专家
    "StockQuoteExpert",
    "StockStrategyExpert",
    "StockTradingExpert",
    "StockRiskExpert",
    "StockBacktestExpert",
    "StockPredictionExpert",
    "StockPortfolioExpert",
    "get_stock_experts",
    # 运营财务专家
    "OperationsAnalysisExpert",
    "UserAnalysisExpert",
    "ActivityExpert",
    "ChannelExpert",
    "FinanceAccountingExpert",
    "CostManagementExpert",
    "BudgetExpert",
    "ReportExpert",
    "TaxExpert",
    "RiskControlExpert",
    "get_operations_finance_experts",
    # 编程专家
    "CodeGenerationExpert",
    "CodeReviewExpert",
    "PerformanceOptimizationExpert",
    "BugFixExpert",
    "DocumentationExpert",
    "get_coding_experts",
    "ExpertCollaborationHub",
    "get_all_experts",
    "get_expert_count",
]


def get_all_experts() -> Dict[str, Any]:
    """
    汇总全部专家实例，便于统一检索/统计
    """
    experts: Dict[str, Any] = {}
    
    # 为每个模块的专家键名添加前缀以避免冲突
    rag_experts = get_rag_experts()
    erp_experts = get_erp_experts()
    content_experts = get_content_experts()
    trend_experts = get_trend_experts()
    stock_experts = get_stock_experts()
    operations_finance_experts = get_operations_finance_experts()
    coding_experts = get_coding_experts()
    
    # 添加前缀并合并
    experts.update({f"rag_{k}": v for k, v in rag_experts.items()})
    experts.update({f"erp_{k}": v for k, v in erp_experts.items()})
    experts.update({f"content_{k}": v for k, v in content_experts.items()})
    experts.update({f"trend_{k}": v for k, v in trend_experts.items()})
    experts.update({f"stock_{k}": v for k, v in stock_experts.items()})
    experts.update({f"finance_{k}": v for k, v in operations_finance_experts.items()})
    experts.update({f"coding_{k}": v for k, v in coding_experts.items()})
    
    return experts


def get_expert_count() -> int:
    """返回登记的专家数量"""
    return len(get_all_experts())
