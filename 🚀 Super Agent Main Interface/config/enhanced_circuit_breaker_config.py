"""
增强限流熔断配置
定义动态熔断、智能限流、服务降级和恢复策略的配置
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from ..core.enhanced_circuit_breaker import (
    EnhancedCircuitState, DynamicThresholdStrategy, DegradationStrategy
)
from ..core.enhanced_rate_limiter import RateLimitConfig, RateLimitAlgorithm, RateLimitPriority
from ..core.service_degradation_recovery import (
    DegradationLevel, RecoveryStrategy, DegradationRule, RecoveryRule
)


class ServiceCategory(Enum):
    """服务分类"""
    API_SERVICE = "api_service"  # API服务
    DATABASE_SERVICE = "database_service"  # 数据库服务
    EXTERNAL_SERVICE = "external_service"  # 外部服务
    INTERNAL_SERVICE = "internal_service"  # 内部服务
    CRITICAL_SERVICE = "critical_service"  # 关键服务


@dataclass
class EnhancedCircuitBreakerConfig:
    """增强熔断器配置"""
    name: str  # 熔断器名称
    base_failure_threshold: float = 0.5  # 基础失败阈值
    recovery_timeout: int = 60  # 恢复超时（秒）
    half_open_max_requests: int = 3  # 半开状态最大请求数
    threshold_strategy: DynamicThresholdStrategy = DynamicThresholdStrategy.ADAPTIVE
    service_category: ServiceCategory = ServiceCategory.API_SERVICE
    
    # 降级策略配置
    enable_degradation: bool = True
    degradation_threshold: float = 0.7  # 降级阈值（失败阈值的百分比）
    fallback_enabled: bool = True


@dataclass
class EnhancedRateLimitConfig:
    """增强限流配置"""
    name: str  # 限流器名称
    max_requests: int  # 最大请求数
    time_window: int  # 时间窗口（秒）
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.ADAPTIVE
    priority_based: bool = False  # 是否基于优先级
    service_category: ServiceCategory = ServiceCategory.API_SERVICE
    
    # 优先级配额配置（仅当priority_based=True时生效）
    low_priority_quota: float = 0.2  # 低优先级配额
    normal_priority_quota: float = 0.5  # 正常优先级配额
    high_priority_quota: float = 0.2  # 高优先级配额
    critical_priority_quota: float = 0.1  # 关键优先级配额


@dataclass
class ServiceDegradationConfig:
    """服务降级配置"""
    feature_name: str  # 功能名称
    service_category: ServiceCategory  # 服务分类
    
    # 降级规则
    degradation_rules: List[DegradationRule]
    
    # 恢复规则
    recovery_rules: List[RecoveryRule]
    
    # 重试策略
    max_retries: int = 3
    base_retry_delay: float = 1.0
    enable_jitter: bool = True


@dataclass
class ServiceProtectionConfig:
    """服务保护配置"""
    service_name: str  # 服务名称
    category: ServiceCategory  # 服务分类
    
    # 熔断器配置
    circuit_breaker_config: EnhancedCircuitBreakerConfig
    
    # 限流器配置
    rate_limit_config: EnhancedRateLimitConfig
    
    # 降级配置
    degradation_config: ServiceDegradationConfig
    
    # 监控配置
    enable_monitoring: bool = True
    metrics_collection_interval: int = 30  # 指标收集间隔（秒）


# 预定义配置模板
class EnhancedCircuitBreakerTemplates:
    """增强熔断器配置模板"""
    
    @staticmethod
    def create_api_service_config(service_name: str) -> EnhancedCircuitBreakerConfig:
        """创建API服务熔断器配置"""
        return EnhancedCircuitBreakerConfig(
            name=f"{service_name}_api_circuit",
            base_failure_threshold=0.3,  # API服务更敏感
            recovery_timeout=30,
            threshold_strategy=DynamicThresholdStrategy.ADAPTIVE,
            service_category=ServiceCategory.API_SERVICE
        )
    
    @staticmethod
    def create_database_service_config(service_name: str) -> EnhancedCircuitBreakerConfig:
        """创建数据库服务熔断器配置"""
        return EnhancedCircuitBreakerConfig(
            name=f"{service_name}_db_circuit",
            base_failure_threshold=0.2,  # 数据库服务非常敏感
            recovery_timeout=120,  # 更长恢复时间
            threshold_strategy=DynamicThresholdStrategy.STATIC,  # 数据库使用静态阈值
            service_category=ServiceCategory.DATABASE_SERVICE
        )
    
    @staticmethod
    def create_external_service_config(service_name: str) -> EnhancedCircuitBreakerConfig:
        """创建外部服务熔断器配置"""
        return EnhancedCircuitBreakerConfig(
            name=f"{service_name}_external_circuit",
            base_failure_threshold=0.4,
            recovery_timeout=60,
            threshold_strategy=DynamicThresholdStrategy.PREDICTIVE,  # 外部服务使用预测性阈值
            service_category=ServiceCategory.EXTERNAL_SERVICE
        )
    
    @staticmethod
    def create_critical_service_config(service_name: str) -> EnhancedCircuitBreakerConfig:
        """创建关键服务熔断器配置"""
        return EnhancedCircuitBreakerConfig(
            name=f"{service_name}_critical_circuit",
            base_failure_threshold=0.1,  # 关键服务非常敏感
            recovery_timeout=10,  # 快速恢复
            threshold_strategy=DynamicThresholdStrategy.ADAPTIVE,
            service_category=ServiceCategory.CRITICAL_SERVICE
        )


class EnhancedRateLimitTemplates:
    """增强限流配置模板"""
    
    @staticmethod
    def create_high_traffic_api_config(service_name: str) -> EnhancedRateLimitConfig:
        """创建高流量API限流配置"""
        return EnhancedRateLimitConfig(
            name=f"{service_name}_api_rate_limit",
            max_requests=1000,  # 每秒1000请求
            time_window=60,
            algorithm=RateLimitAlgorithm.ADAPTIVE,
            priority_based=True,
            service_category=ServiceCategory.API_SERVICE
        )
    
    @staticmethod
    def create_user_rate_limit_config(service_name: str) -> EnhancedRateLimitConfig:
        """创建用户级限流配置"""
        return EnhancedRateLimitConfig(
            name=f"{service_name}_user_rate_limit",
            max_requests=100,  # 每秒100请求
            time_window=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            priority_based=False,
            service_category=ServiceCategory.API_SERVICE
        )
    
    @staticmethod
    def create_database_rate_limit_config(service_name: str) -> EnhancedRateLimitConfig:
        """创建数据库限流配置"""
        return EnhancedRateLimitConfig(
            name=f"{service_name}_db_rate_limit",
            max_requests=500,  # 数据库查询限制
            time_window=60,
            algorithm=RateLimitAlgorithm.LEAKY_BUCKET,  # 数据库适合漏桶算法
            priority_based=True,
            service_category=ServiceCategory.DATABASE_SERVICE
        )
    
    @staticmethod
    def create_critical_rate_limit_config(service_name: str) -> EnhancedRateLimitConfig:
        """创建关键服务限流配置"""
        return EnhancedRateLimitConfig(
            name=f"{service_name}_critical_rate_limit",
            max_requests=50,  # 关键服务限制较少但保证可用
            time_window=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            priority_based=True,
            service_category=ServiceCategory.CRITICAL_SERVICE
        )


class ServiceDegradationTemplates:
    """服务降级配置模板"""
    
    @staticmethod
    def create_api_degradation_config(service_name: str) -> ServiceDegradationConfig:
        """创建API服务降级配置"""
        from ..core.service_degradation_recovery import (
            high_error_rate_condition, high_latency_condition,
            low_error_rate_condition, normal_latency_condition
        )
        
        return ServiceDegradationConfig(
            feature_name=f"{service_name}_api",
            service_category=ServiceCategory.API_SERVICE,
            degradation_rules=[
                DegradationRule(
                    feature_name=f"{service_name}_api",
                    degradation_level=DegradationLevel.PARTIAL,
                    fallback_func=None,
                    conditions=[high_error_rate_condition, high_latency_condition],
                    priority=1
                )
            ],
            recovery_rules=[
                RecoveryRule(
                    feature_name=f"{service_name}_api",
                    recovery_strategy=RecoveryStrategy.INTELLIGENT,
                    conditions=[low_error_rate_condition, normal_latency_condition],
                    retry_delay=2.0,
                    max_retries=5
                )
            ]
        )
    
    @staticmethod
    def create_database_degradation_config(service_name: str) -> ServiceDegradationConfig:
        """创建数据库服务降级配置"""
        from ..core.service_degradation_recovery import (
            high_error_rate_condition, system_overload_condition,
            low_error_rate_condition, system_normal_condition
        )
        
        return ServiceDegradationConfig(
            feature_name=f"{service_name}_database",
            service_category=ServiceCategory.DATABASE_SERVICE,
            degradation_rules=[
                DegradationRule(
                    feature_name=f"{service_name}_database",
                    degradation_level=DegradationLevel.FULL,  # 数据库故障时完全降级
                    fallback_func=None,
                    conditions=[high_error_rate_condition, system_overload_condition],
                    priority=1
                )
            ],
            recovery_rules=[
                RecoveryRule(
                    feature_name=f"{service_name}_database",
                    recovery_strategy=RecoveryStrategy.GRADUAL,  # 数据库渐进恢复
                    conditions=[low_error_rate_condition, system_normal_condition],
                    retry_delay=5.0,  # 数据库恢复较慢
                    max_retries=3
                )
            ]
        )


# 默认配置
DEFAULT_CIRCUIT_BREAKER_CONFIGS: Dict[ServiceCategory, EnhancedCircuitBreakerConfig] = {
    ServiceCategory.API_SERVICE: EnhancedCircuitBreakerTemplates.create_api_service_config("default"),
    ServiceCategory.DATABASE_SERVICE: EnhancedCircuitBreakerTemplates.create_database_service_config("default"),
    ServiceCategory.EXTERNAL_SERVICE: EnhancedCircuitBreakerTemplates.create_external_service_config("default"),
    ServiceCategory.CRITICAL_SERVICE: EnhancedCircuitBreakerTemplates.create_critical_service_config("default")
}

DEFAULT_RATE_LIMIT_CONFIGS: Dict[ServiceCategory, EnhancedRateLimitConfig] = {
    ServiceCategory.API_SERVICE: EnhancedRateLimitTemplates.create_high_traffic_api_config("default"),
    ServiceCategory.DATABASE_SERVICE: EnhancedRateLimitTemplates.create_database_rate_limit_config("default"),
    ServiceCategory.CRITICAL_SERVICE: EnhancedRateLimitTemplates.create_critical_rate_limit_config("default")
}

DEFAULT_DEGRADATION_CONFIGS: Dict[ServiceCategory, ServiceDegradationConfig] = {
    ServiceCategory.API_SERVICE: ServiceDegradationTemplates.create_api_degradation_config("default"),
    ServiceCategory.DATABASE_SERVICE: ServiceDegradationTemplates.create_database_degradation_config("default")
}


class EnhancedCircuitBreakerConfigManager:
    """增强熔断器配置管理器"""
    
    def __init__(self):
        self.service_configs: Dict[str, ServiceProtectionConfig] = {}
    
    def register_service(self, service_name: str, category: ServiceCategory,
                        custom_config: Optional[ServiceProtectionConfig] = None) -> ServiceProtectionConfig:
        """注册服务配置"""
        if custom_config:
            self.service_configs[service_name] = custom_config
            return custom_config
        
        # 使用默认配置
        config = ServiceProtectionConfig(
            service_name=service_name,
            category=category,
            circuit_breaker_config=DEFAULT_CIRCUIT_BREAKER_CONFIGS[category],
            rate_limit_config=DEFAULT_RATE_LIMIT_CONFIGS.get(category, DEFAULT_RATE_LIMIT_CONFIGS[ServiceCategory.API_SERVICE]),
            degradation_config=DEFAULT_DEGRADATION_CONFIGS.get(category, DEFAULT_DEGRADATION_CONFIGS[ServiceCategory.API_SERVICE])
        )
        
        self.service_configs[service_name] = config
        return config
    
    def get_service_config(self, service_name: str) -> Optional[ServiceProtectionConfig]:
        """获取服务配置"""
        return self.service_configs.get(service_name)
    
    def get_all_configs(self) -> Dict[str, ServiceProtectionConfig]:
        """获取所有配置"""
        return self.service_configs.copy()
    
    def update_service_config(self, service_name: str, 
                             config_updates: Dict[str, Any]) -> bool:
        """更新服务配置"""
        config = self.service_configs.get(service_name)
        if not config:
            return False
        
        # 更新配置（简化实现）
        for key, value in config_updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return True


# 全局配置管理器实例
enhanced_config_manager = EnhancedCircuitBreakerConfigManager()