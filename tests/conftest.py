"""
测试公共配置，确保可以导入 core 模块
"""

import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
ASCII_LINK = WORKSPACE_ROOT / "super_agent_main_interface"

# 在模块级别就设置路径，确保导入时可用
for candidate in (PROJECT_ROOT, ASCII_LINK):
    if candidate.exists():
        path_str = str(candidate.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def pytest_configure(config):
    """
    pytest 配置 hook，在收集测试之前执行
    确保路径已设置，即使测试文件在 conftest 之前被导入
    """
    for candidate in (PROJECT_ROOT, ASCII_LINK):
        if candidate.exists():
            path_str = str(candidate.resolve())
            if path_str not in sys.path:
                sys.path.insert(0, path_str)


@pytest.fixture()
def writable_tmp_path(tmp_path):
    """
    直接复用 pytest 提供的 tmp_path；真正写入前会在测试内部二次检测。
    """
    return tmp_path


# 趋势分析专家模块特定配置
@pytest.fixture
def trend_data_connector():
    """提供趋势数据连接器fixture"""
    from core.experts.trend_experts import TrendDataConnector
    return TrendDataConnector()


@pytest.fixture
def trend_collection_expert(trend_data_connector):
    """提供趋势采集专家fixture"""
    from core.experts.trend_experts import TrendCollectionExpert
    return TrendCollectionExpert(trend_data_connector)


@pytest.fixture
def trend_processing_expert(trend_data_connector):
    """提供趋势处理专家fixture"""
    from core.experts.trend_experts import TrendProcessingExpert
    return TrendProcessingExpert(trend_data_connector)


@pytest.fixture
def trend_analysis_expert(trend_data_connector):
    """提供趋势分析专家fixture"""
    from core.experts.trend_experts import TrendAnalysisExpert
    return TrendAnalysisExpert(trend_data_connector)


@pytest.fixture
def trend_prediction_expert(trend_data_connector):
    """提供趋势预测专家fixture"""
    from core.experts.trend_experts import TrendPredictionExpert
    return TrendPredictionExpert(trend_data_connector)


@pytest.fixture
def trend_report_expert(trend_data_connector):
    """提供趋势报告专家fixture"""
    from core.experts.trend_experts import TrendReportExpert
    return TrendReportExpert(trend_data_connector)


@pytest.fixture
def trend_alert_expert(trend_data_connector):
    """提供趋势预警专家fixture"""
    from core.experts.trend_experts import TrendAlertExpert
    return TrendAlertExpert(trend_data_connector)


@pytest.fixture
def all_trend_experts(trend_data_connector):
    """提供所有趋势专家fixture"""
    from core.experts.trend_experts import get_trend_experts
    return get_trend_experts(trend_data_connector)


@pytest.fixture
def sample_trend_data():
    """提供示例趋势数据"""
    return {
        "trends": [
            {
                "id": 1,
                "name": "AI技术发展",
                "strength": 0.85,
                "direction": "up",
                "volatility": 0.3,
                "values": [100, 120, 150, 180, 200]
            },
            {
                "id": 2,
                "name": "区块链应用",
                "strength": 0.6,
                "direction": "stable",
                "volatility": 0.5,
                "values": [80, 75, 85, 70, 90]
            }
        ],
        "patterns": [
            {
                "id": 1,
                "type": "seasonal",
                "confidence": 0.9,
                "period": 12
            }
        ]
    }


@pytest.fixture
def sample_alert_data():
    """提供示例预警数据"""
    return {
        "alerts": [
            {
                "id": 1,
                "level": "high",
                "message": "高风险：趋势波动异常",
                "timestamp": "2024-01-01 10:00:00",
                "severity": 0.9
            },
            {
                "id": 2,
                "level": "medium",
                "message": "中风险：数据质量下降",
                "timestamp": "2024-01-01 11:00:00",
                "severity": 0.6
            }
        ],
        "accuracy": 0.85,
        "avg_response_time": 8.5
    }


@pytest.fixture
def sample_prediction_data():
    """提供示例预测数据"""
    return {
        "historical_data": {
            "trends": [
                {
                    "id": 1,
                    "values": [10, 20, 30, 40, 50],
                    "timestamps": [1, 2, 3, 4, 5]
                }
            ]
        },
        "prediction_horizon": 3,
        "confidence_threshold": 0.7
    }


@pytest.fixture
def performance_test_config():
    """性能测试配置"""
    return {
        "slo_threshold": 2.0,  # 2秒SLO要求
        "max_iterations": 10,  # 最大迭代次数
        "warmup_iterations": 3  # 预热迭代
    }


def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--performance",
        action="store_true",
        default=False,
        help="运行性能测试"
    )
    parser.addoption(
        "--integration",
        action="store_true", 
        default=False,
        help="运行集成测试"
    )


def pytest_collection_modifyitems(config, items):
    """根据命令行选项过滤测试项"""
    if config.getoption("--performance"):
        # 只运行性能测试
        skip_non_performance = pytest.mark.skip(reason="非性能测试")
        for item in items:
            if "performance" not in item.name:
                item.add_marker(skip_non_performance)
    
    if config.getoption("--integration"):
        # 只运行集成测试
        skip_non_integration = pytest.mark.skip(reason="非集成测试")
        for item in items:
            if "integration" not in item.name:
                item.add_marker(skip_non_integration)


