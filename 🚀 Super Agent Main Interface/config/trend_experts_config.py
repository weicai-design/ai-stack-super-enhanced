"""
趋势分析专家模块配置管理

管理趋势分析专家模块的所有配置参数，包括：
1. 数据连接器配置
2. 专家性能配置
3. 预警阈值配置
4. 分析深度配置
5. API配置

支持环境变量覆盖和动态配置更新
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import yaml
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DataConnectorConfig:
    """数据连接器配置"""
    # 平台连接配置
    platforms: Dict[str, Dict[str, Any]] = None
    
    # 连接超时配置（秒）
    connection_timeout: int = 30
    
    # 重试配置
    max_retries: int = 3
    retry_delay: int = 5
    
    # 数据缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5分钟
    
    # 实时数据更新间隔（秒）
    realtime_update_interval: int = 60
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = {
                "financial": {
                    "enabled": True,
                    "priority": 1,
                    "api_endpoint": os.getenv("FINANCIAL_API_ENDPOINT", "https://api.financial.com"),
                    "api_key": os.getenv("FINANCIAL_API_KEY", "default_key"),
                    "rate_limit": 100
                },
                "social_media": {
                    "enabled": True,
                    "priority": 2,
                    "api_endpoint": os.getenv("SOCIAL_MEDIA_API_ENDPOINT", "https://api.social.com"),
                    "api_key": os.getenv("SOCIAL_MEDIA_API_KEY", "default_key"),
                    "rate_limit": 200
                },
                "news": {
                    "enabled": True,
                    "priority": 3,
                    "api_endpoint": os.getenv("NEWS_API_ENDPOINT", "https://api.news.com"),
                    "api_key": os.getenv("NEWS_API_KEY", "default_key"),
                    "rate_limit": 150
                },
                "market": {
                    "enabled": True,
                    "priority": 4,
                    "api_endpoint": os.getenv("MARKET_API_ENDPOINT", "https://api.market.com"),
                    "api_key": os.getenv("MARKET_API_KEY", "default_key"),
                    "rate_limit": 80
                },
                "research": {
                    "enabled": True,
                    "priority": 5,
                    "api_endpoint": os.getenv("RESEARCH_API_ENDPOINT", "https://api.research.com"),
                    "api_key": os.getenv("RESEARCH_API_KEY", "default_key"),
                    "rate_limit": 50
                }
            }


@dataclass
class PerformanceConfig:
    """性能配置"""
    # SLO配置（秒）
    slo_threshold: float = 2.0
    
    # 异步处理配置
    max_concurrent_tasks: int = 10
    task_timeout: int = 30
    
    # 内存使用限制（MB）
    memory_limit_mb: int = 512
    
    # CPU使用限制
    cpu_usage_limit: float = 0.8
    
    # 监控配置
    monitoring_enabled: bool = True
    metrics_interval: int = 60  # 秒


@dataclass
class AlertConfig:
    """预警配置"""
    # 预警阈值配置
    thresholds: Dict[str, float] = None
    
    # 预警级别配置
    levels: Dict[str, Dict[str, Any]] = None
    
    # 响应时间配置（秒）
    response_time_warning: int = 10
    response_time_critical: int = 30
    
    # 通知配置
    notification_enabled: bool = True
    notification_channels: list = None
    
    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = {
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4
            }
        
        if self.levels is None:
            self.levels = {
                "high": {
                    "color": "red",
                    "priority": 1,
                    "auto_escalate": True
                },
                "medium": {
                    "color": "orange",
                    "priority": 2,
                    "auto_escalate": False
                },
                "low": {
                    "color": "yellow",
                    "priority": 3,
                    "auto_escalate": False
                }
            }
        
        if self.notification_channels is None:
            self.notification_channels = ["email", "slack"]


@dataclass
class AnalysisConfig:
    """分析配置"""
    # 分析深度配置
    analysis_depths: Dict[str, Dict[str, Any]] = None
    
    # 趋势识别配置
    trend_identification: Dict[str, Any] = None
    
    # 模式发现配置
    pattern_discovery: Dict[str, Any] = None
    
    # 关联分析配置
    correlation_analysis: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.analysis_depths is None:
            self.analysis_depths = {
                "basic": {
                    "max_trends": 10,
                    "max_patterns": 5,
                    "time_window": 7  # 天
                },
                "standard": {
                    "max_trends": 50,
                    "max_patterns": 20,
                    "time_window": 30
                },
                "deep": {
                    "max_trends": 100,
                    "max_patterns": 50,
                    "time_window": 90
                }
            }
        
        if self.trend_identification is None:
            self.trend_identification = {
                "min_strength": 0.3,
                "min_duration": 3,  # 天
                "volatility_threshold": 0.5
            }
        
        if self.pattern_discovery is None:
            self.pattern_discovery = {
                "min_confidence": 0.7,
                "min_support": 0.1,
                "max_pattern_length": 10
            }
        
        if self.correlation_analysis is None:
            self.correlation_analysis = {
                "min_correlation": 0.5,
                "max_lag": 7,  # 天
                "significance_level": 0.05
            }


@dataclass
class PredictionConfig:
    """预测配置"""
    # 预测模型配置
    models: Dict[str, Dict[str, Any]] = None
    
    # 预测周期配置（天）
    prediction_horizons: Dict[str, int] = None
    
    # 置信度配置
    confidence_levels: Dict[str, float] = None
    
    # 风险评估配置
    risk_assessment: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = {
                "arima": {
                    "enabled": True,
                    "order": (1, 1, 1),
                    "seasonal_order": (1, 1, 1, 12)
                },
                "prophet": {
                    "enabled": True,
                    "changepoint_prior_scale": 0.05,
                    "seasonality_prior_scale": 10.0
                },
                "lstm": {
                    "enabled": False,
                    "hidden_units": 50,
                    "epochs": 100
                }
            }
        
        if self.prediction_horizons is None:
            self.prediction_horizons = {
                "short_term": 7,
                "medium_term": 30,
                "long_term": 90
            }
        
        if self.confidence_levels is None:
            self.confidence_levels = {
                "high": 0.9,
                "medium": 0.7,
                "low": 0.5
            }
        
        if self.risk_assessment is None:
            self.risk_assessment = {
                "volatility_threshold": 0.3,
                "anomaly_threshold": 0.8,
                "stability_threshold": 0.6
            }


@dataclass
class ReportConfig:
    """报告配置"""
    # 报告格式配置
    formats: Dict[str, Dict[str, Any]] = None
    
    # 可视化配置
    visualizations: Dict[str, Any] = None
    
    # 洞察提取配置
    insight_extraction: Dict[str, Any] = None
    
    # 导出配置
    export_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = {
                "standard": {
                    "sections": ["executive_summary", "trend_analysis", "predictions", "recommendations"],
                    "max_length": 10  # 页
                },
                "detailed": {
                    "sections": ["executive_summary", "methodology", "trend_analysis", "pattern_analysis", "predictions", "risk_assessment", "recommendations"],
                    "max_length": 25
                },
                "executive": {
                    "sections": ["executive_summary", "key_insights", "recommendations"],
                    "max_length": 5
                }
            }
        
        if self.visualizations is None:
            self.visualizations = {
                "chart_types": ["line", "bar", "scatter", "heatmap"],
                "color_scheme": "viridis",
                "interactive": True
            }
        
        if self.insight_extraction is None:
            self.insight_extraction = {
                "min_significance": 0.7,
                "max_insights": 10,
                "categorization_enabled": True
            }
        
        if self.export_options is None:
            self.export_options = {
                "formats": ["pdf", "html", "json"],
                "compression_enabled": True,
                "watermark_enabled": False
            }


@dataclass
class APIConfig:
    """API配置"""
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 安全配置
    cors_enabled: bool = True
    rate_limit_enabled: bool = True
    
    # 日志配置
    log_level: str = "info"
    access_log_enabled: bool = True
    
    # 监控配置
    metrics_enabled: bool = True
    health_check_interval: int = 30  # 秒


@dataclass
class TrendExpertsConfig:
    """趋势分析专家模块主配置"""
    # 模块版本
    version: str = "1.0.0"
    
    # 环境配置
    environment: str = "development"
    debug_mode: bool = False
    
    # 子配置
    data_connector: DataConnectorConfig = None
    performance: PerformanceConfig = None
    alerts: AlertConfig = None
    analysis: AnalysisConfig = None
    prediction: PredictionConfig = None
    report: ReportConfig = None
    api: APIConfig = None
    
    def __post_init__(self):
        if self.data_connector is None:
            self.data_connector = DataConnectorConfig()
        
        if self.performance is None:
            self.performance = PerformanceConfig()
        
        if self.alerts is None:
            self.alerts = AlertConfig()
        
        if self.analysis is None:
            self.analysis = AnalysisConfig()
        
        if self.prediction is None:
            self.prediction = PredictionConfig()
        
        if self.report is None:
            self.report = ReportConfig()
        
        if self.api is None:
            self.api = APIConfig()


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> TrendExpertsConfig:
        """加载配置"""
        # 从环境变量获取配置
        environment = os.getenv("TREND_EXPERTS_ENV", "development")
        debug_mode = os.getenv("TREND_EXPERTS_DEBUG", "false").lower() == "true"
        
        # 创建默认配置
        config = TrendExpertsConfig(
            environment=environment,
            debug_mode=debug_mode
        )
        
        # 如果提供了配置文件，从文件加载配置
        if self.config_file and os.path.exists(self.config_file):
            config = self._load_from_file(self.config_file, config)
        
        # 应用环境变量覆盖
        config = self._apply_env_overrides(config)
        
        logger.info(f"趋势分析专家模块配置加载完成 - 环境: {environment}")
        
        return config
    
    def _load_from_file(self, config_file: str, base_config: TrendExpertsConfig) -> TrendExpertsConfig:
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    file_config = yaml.safe_load(f)
                elif config_file.endswith('.json'):
                    file_config = json.load(f)
                else:
                    logger.warning(f"不支持的配置文件格式: {config_file}")
                    return base_config
            
            # 将文件配置应用到基础配置
            return self._merge_configs(base_config, file_config)
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return base_config
    
    def _merge_configs(self, base_config: TrendExpertsConfig, file_config: Dict[str, Any]) -> TrendExpertsConfig:
        """合并配置"""
        # 将基础配置转换为字典
        base_dict = asdict(base_config)
        
        # 递归合并配置
        def merge_dicts(base, update):
            for key, value in update.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value
            return base
        
        merged_dict = merge_dicts(base_dict, file_config)
        
        # 将合并后的字典转换回配置对象
        return TrendExpertsConfig(**merged_dict)
    
    def _apply_env_overrides(self, config: TrendExpertsConfig) -> TrendExpertsConfig:
        """应用环境变量覆盖"""
        # API配置覆盖
        config.api.host = os.getenv("TREND_API_HOST", config.api.host)
        config.api.port = int(os.getenv("TREND_API_PORT", str(config.api.port)))
        
        # 性能配置覆盖
        config.performance.slo_threshold = float(os.getenv("SLO_THRESHOLD", str(config.performance.slo_threshold)))
        
        # 数据连接器配置覆盖
        for platform in config.data_connector.platforms:
            env_key = f"{platform.upper()}_API_ENDPOINT"
            if env_key in os.environ:
                config.data_connector.platforms[platform]["api_endpoint"] = os.environ[env_key]
        
        return config
    
    def get_config(self) -> TrendExpertsConfig:
        """获取当前配置"""
        return self.config
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self.config = self._merge_configs(self.config, new_config)
            logger.info("配置更新成功")
            return True
        except Exception as e:
            logger.error(f"配置更新失败: {str(e)}")
            return False
    
    def save_config(self, file_path: str) -> bool:
        """保存配置到文件"""
        try:
            config_dict = asdict(self.config)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                elif file_path.endswith('.json'):
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:
                    logger.error(f"不支持的配置文件格式: {file_path}")
                    return False
            
            logger.info(f"配置已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    
    return _config_manager


def get_config() -> TrendExpertsConfig:
    """获取当前配置"""
    return get_config_manager().get_config()


def reload_config(config_file: Optional[str] = None) -> bool:
    """重新加载配置"""
    global _config_manager
    
    try:
        _config_manager = ConfigManager(config_file)
        logger.info("配置重新加载成功")
        return True
    except Exception as e:
        logger.error(f"配置重新加载失败: {str(e)}")
        return False


# 默认配置导出
default_config = TrendExpertsConfig()


if __name__ == "__main__":
    # 测试配置管理功能
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    print("趋势分析专家模块配置:")
    print(f"版本: {config.version}")
    print(f"环境: {config.environment}")
    print(f"数据平台数量: {len(config.data_connector.platforms)}")
    print(f"SLO阈值: {config.performance.slo_threshold}秒")
    
    # 保存配置示例
    config_manager.save_config("trend_experts_config.yaml")