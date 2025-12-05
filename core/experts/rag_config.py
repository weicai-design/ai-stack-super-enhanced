"""
RAG专家配置管理系统
为RAG专家模块提供生产级配置管理和监控支持
"""

import os
import json
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGExpertType(Enum):
    """RAG专家类型"""
    KNOWLEDGE = "knowledge"
    RETRIEVAL = "retrieval"
    GRAPH = "graph"


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RAGExpertConfig:
    """RAG专家基础配置"""
    
    # 质量阈值
    quality_threshold: float = 0.7
    high_quality_threshold: float = 0.8
    
    # 处理配置
    max_processing_time: float = 30.0
    batch_size: int = 100
    
    # 日志配置
    enable_logging: bool = True
    log_level: str = "debug"
    
    # 监控配置
    enable_monitoring: bool = True
    enable_tracing: bool = True
    
    # 专家特定配置
    expert_specific: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RAGExpertConfig':
        """从字典创建配置"""
        return cls(
            quality_threshold=data.get('quality_threshold', 0.7),
            high_quality_threshold=data.get('high_quality_threshold', 0.8),
            max_processing_time=data.get('max_processing_time', 30.0),
            batch_size=data.get('batch_size', 100),
            enable_logging=data.get('enable_logging', True),
            log_level=data.get('log_level', 'debug'),
            enable_monitoring=data.get('enable_monitoring', True),
            enable_tracing=data.get('enable_tracing', True),
            expert_specific=data.get('expert_specific', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'quality_threshold': self.quality_threshold,
            'high_quality_threshold': self.high_quality_threshold,
            'max_processing_time': self.max_processing_time,
            'batch_size': self.batch_size,
            'enable_logging': self.enable_logging,
            'log_level': self.log_level,
            'enable_monitoring': self.enable_monitoring,
            'enable_tracing': self.enable_tracing,
            'expert_specific': self.expert_specific
        }


@dataclass
class RAGSystemConfig:
    """RAG系统整体配置"""
    
    # 并发配置
    max_concurrent_requests: int = 10
    request_timeout: float = 60.0
    retry_attempts: int = 3
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    # 监控配置
    monitoring_enabled: bool = True
    metrics_port: int = 9090
    health_check_port: int = 8080
    
    # 专家配置
    experts: Dict[str, RAGExpertConfig] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RAGSystemConfig':
        """从字典创建配置"""
        experts = {}
        for expert_id, expert_config in data.get('experts', {}).items():
            experts[expert_id] = RAGExpertConfig.from_dict(expert_config)
        
        return cls(
            max_concurrent_requests=data.get('max_concurrent_requests', 10),
            request_timeout=data.get('request_timeout', 60.0),
            retry_attempts=data.get('retry_attempts', 3),
            cache_enabled=data.get('cache_enabled', True),
            cache_ttl=data.get('cache_ttl', 3600),
            monitoring_enabled=data.get('monitoring_enabled', True),
            metrics_port=data.get('metrics_port', 9090),
            health_check_port=data.get('health_check_port', 8080),
            experts=experts
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'max_concurrent_requests': self.max_concurrent_requests,
            'request_timeout': self.request_timeout,
            'retry_attempts': self.retry_attempts,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'monitoring_enabled': self.monitoring_enabled,
            'metrics_port': self.metrics_port,
            'health_check_port': self.health_check_port,
            'experts': {expert_id: config.to_dict() 
                       for expert_id, config in self.experts.items()}
        }


class RAGConfigManager:
    """RAG配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[RAGSystemConfig] = None
        self._last_modified: Optional[float] = None
        
    def _get_default_config_path(self) -> str:
        """获取默认配置路径"""
        # 优先检查环境变量
        env_config = os.getenv('RAG_CONFIG_PATH')
        if env_config:
            return env_config
        
        # 检查项目配置目录
        project_root = Path(__file__).parent.parent.parent
        config_dir = project_root / 'config'
        
        # 按优先级检查配置文件
        config_files = [
            config_dir / 'rag_experts_config.yaml',
            config_dir / 'rag_experts_config.json',
            config_dir / 'rag_config.yaml',
            config_dir / 'rag_config.json'
        ]
        
        for config_file in config_files:
            if config_file.exists():
                return str(config_file)
        
        # 默认使用环境配置
        return str(config_dir / 'rag_experts_config.yaml')
    
    def load_config(self) -> RAGSystemConfig:
        """加载配置"""
        config_path = Path(self.config_path)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}, 使用默认配置")
            return self._get_default_config()
        
        # 检查文件是否已修改
        current_mtime = config_path.stat().st_mtime
        if self._config and self._last_modified == current_mtime:
            return self._config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml':
                    config_data = yaml.safe_load(f) or {}
                else:
                    config_data = json.load(f)
            
            # 从文件加载配置
            self._config = RAGSystemConfig.from_dict(config_data)
            
            # 应用环境变量覆盖
            self._apply_environment_overrides()
            
            self._last_modified = current_mtime
            logger.info(f"成功加载RAG配置: {config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}, 使用默认配置")
            self._config = self._get_default_config()
        
        return self._config
    
    def _apply_environment_overrides(self):
        """应用环境变量覆盖到当前配置"""
        if not self._config:
            return
        
        # 系统级配置覆盖
        if os.getenv('RAG_MAX_CONCURRENT_REQUESTS'):
            self._config.max_concurrent_requests = int(os.getenv('RAG_MAX_CONCURRENT_REQUESTS'))
        if os.getenv('RAG_REQUEST_TIMEOUT'):
            self._config.request_timeout = float(os.getenv('RAG_REQUEST_TIMEOUT'))
        if os.getenv('RAG_RETRY_ATTEMPTS'):
            self._config.retry_attempts = int(os.getenv('RAG_RETRY_ATTEMPTS'))
        if os.getenv('RAG_CACHE_ENABLED'):
            self._config.cache_enabled = os.getenv('RAG_CACHE_ENABLED').lower() == 'true'
        if os.getenv('RAG_CACHE_TTL'):
            self._config.cache_ttl = int(os.getenv('RAG_CACHE_TTL'))
        if os.getenv('RAG_MONITORING_ENABLED'):
            self._config.monitoring_enabled = os.getenv('RAG_MONITORING_ENABLED').lower() == 'true'
        if os.getenv('RAG_METRICS_PORT'):
            self._config.metrics_port = int(os.getenv('RAG_METRICS_PORT'))
        if os.getenv('RAG_HEALTH_CHECK_PORT'):
            self._config.health_check_port = int(os.getenv('RAG_HEALTH_CHECK_PORT'))
        
        # 专家级配置覆盖
        expert_env_mappings = {
            'knowledge': {
                'quality_threshold': 'KNOWLEDGE_QUALITY_THRESHOLD',
                'high_quality_threshold': 'KNOWLEDGE_HIGH_QUALITY_THRESHOLD',
                'max_processing_time': 'KNOWLEDGE_MAX_PROCESSING_TIME',
                'batch_size': 'KNOWLEDGE_BATCH_SIZE',
                'enable_monitoring': 'KNOWLEDGE_ENABLE_MONITORING',
                'log_level': 'KNOWLEDGE_LOG_LEVEL'
            },
            'retrieval': {
                'quality_threshold': 'RETRIEVAL_QUALITY_THRESHOLD',
                'high_quality_threshold': 'RETRIEVAL_HIGH_QUALITY_THRESHOLD',
                'max_processing_time': 'RETRIEVAL_MAX_PROCESSING_TIME',
                'batch_size': 'RETRIEVAL_BATCH_SIZE',
                'enable_monitoring': 'RETRIEVAL_ENABLE_MONITORING',
                'log_level': 'RETRIEVAL_LOG_LEVEL'
            },
            'graph': {
                'quality_threshold': 'GRAPH_QUALITY_THRESHOLD',
                'high_quality_threshold': 'GRAPH_HIGH_QUALITY_THRESHOLD',
                'max_processing_time': 'GRAPH_MAX_PROCESSING_TIME',
                'batch_size': 'GRAPH_BATCH_SIZE',
                'enable_monitoring': 'GRAPH_ENABLE_MONITORING',
                'log_level': 'GRAPH_LOG_LEVEL'
            }
        }
        
        for expert_id, env_mappings in expert_env_mappings.items():
            if expert_id not in self._config.experts:
                continue
                
            expert_config = self._config.experts[expert_id]
            
            for attr, env_var in env_mappings.items():
                if os.getenv(env_var):
                    env_value = os.getenv(env_var)
                    if attr in ['quality_threshold', 'high_quality_threshold', 'max_processing_time']:
                        setattr(expert_config, attr, float(env_value))
                    elif attr == 'batch_size':
                        setattr(expert_config, attr, int(env_value))
                    elif attr == 'enable_monitoring':
                        setattr(expert_config, attr, env_value.lower() == 'true')
                    elif attr == 'log_level':
                        setattr(expert_config, attr, env_value)
    
    def _get_default_config(self) -> RAGSystemConfig:
        """获取默认配置"""
        # 从环境变量获取配置
        environment = os.getenv('RAG_ENVIRONMENT', 'development')
        
        # 创建默认专家配置
        experts = {
            'knowledge': RAGExpertConfig(
                quality_threshold=float(os.getenv('KNOWLEDGE_QUALITY_THRESHOLD', '0.6')),
                high_quality_threshold=float(os.getenv('KNOWLEDGE_HIGH_QUALITY_THRESHOLD', '0.8')),
                max_processing_time=float(os.getenv('KNOWLEDGE_MAX_PROCESSING_TIME', '30.0')),
                batch_size=int(os.getenv('KNOWLEDGE_BATCH_SIZE', '10')),
                enable_monitoring=os.getenv('KNOWLEDGE_ENABLE_MONITORING', 'true').lower() == 'true',
                log_level=os.getenv('KNOWLEDGE_LOG_LEVEL', 'debug')
            ),
            'retrieval': RAGExpertConfig(
                quality_threshold=float(os.getenv('RETRIEVAL_QUALITY_THRESHOLD', '0.7')),
                high_quality_threshold=float(os.getenv('RETRIEVAL_HIGH_QUALITY_THRESHOLD', '0.85')),
                max_processing_time=float(os.getenv('RETRIEVAL_MAX_PROCESSING_TIME', '20.0')),
                batch_size=int(os.getenv('RETRIEVAL_BATCH_SIZE', '5')),
                enable_monitoring=os.getenv('RETRIEVAL_ENABLE_MONITORING', 'true').lower() == 'true',
                log_level=os.getenv('RETRIEVAL_LOG_LEVEL', 'debug')
            ),
            'graph': RAGExpertConfig(
                quality_threshold=float(os.getenv('GRAPH_QUALITY_THRESHOLD', '0.75')),
                high_quality_threshold=float(os.getenv('GRAPH_HIGH_QUALITY_THRESHOLD', '0.9')),
                max_processing_time=float(os.getenv('GRAPH_MAX_PROCESSING_TIME', '25.0')),
                batch_size=int(os.getenv('GRAPH_BATCH_SIZE', '8')),
                enable_monitoring=os.getenv('GRAPH_ENABLE_MONITORING', 'true').lower() == 'true',
                log_level=os.getenv('GRAPH_LOG_LEVEL', 'debug')
            )
        }
        
        return RAGSystemConfig(
            max_concurrent_requests=int(os.getenv('RAG_MAX_CONCURRENT_REQUESTS', '10')),
            request_timeout=float(os.getenv('RAG_REQUEST_TIMEOUT', '60.0')),
            retry_attempts=int(os.getenv('RAG_RETRY_ATTEMPTS', '3')),
            cache_enabled=os.getenv('RAG_CACHE_ENABLED', 'true').lower() == 'true',
            cache_ttl=int(os.getenv('RAG_CACHE_TTL', '3600')),
            monitoring_enabled=os.getenv('RAG_MONITORING_ENABLED', 'true').lower() == 'true',
            metrics_port=int(os.getenv('RAG_METRICS_PORT', '9090')),
            health_check_port=int(os.getenv('RAG_HEALTH_CHECK_PORT', '8080')),
            experts=experts
        )
    
    def save_config(self, config: RAGSystemConfig, format: str = 'yaml') -> str:
        """保存配置到文件"""
        config_path = Path(self.config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功保存RAG配置: {config_path}")
            return str(config_path)
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def validate_config(self, config: RAGSystemConfig) -> List[str]:
        """验证配置有效性"""
        errors = []
        
        # 验证系统配置
        if config.max_concurrent_requests <= 0:
            errors.append("最大并发请求数必须大于0")
        
        if config.request_timeout <= 0:
            errors.append("请求超时时间必须大于0")
        
        if config.retry_attempts < 0:
            errors.append("重试次数不能为负数")
        
        if config.cache_ttl < 0:
            errors.append("缓存TTL不能为负数")
        
        # 验证专家配置
        for expert_id, expert_config in config.experts.items():
            if expert_config.quality_threshold < 0 or expert_config.quality_threshold > 1:
                errors.append(f"{expert_id}专家质量阈值必须在0-1之间")
            
            if expert_config.high_quality_threshold < 0 or expert_config.high_quality_threshold > 1:
                errors.append(f"{expert_id}专家高质量阈值必须在0-1之间")
            
            if expert_config.max_processing_time <= 0:
                errors.append(f"{expert_id}专家最大处理时间必须大于0")
            
            if expert_config.batch_size <= 0:
                errors.append(f"{expert_id}专家批处理大小必须大于0")
        
        return errors
    
    def get_expert_config(self, expert_id: str) -> RAGExpertConfig:
        """获取特定专家的配置"""
        config = self.load_config()
        return config.experts.get(expert_id, RAGExpertConfig())


# 全局配置管理器实例
_config_manager: Optional[RAGConfigManager] = None


def get_config_manager() -> RAGConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = RAGConfigManager()
    return _config_manager


def get_rag_config() -> RAGSystemConfig:
    """获取RAG系统配置"""
    return get_config_manager().load_config()


def get_expert_config(expert_id: str) -> RAGExpertConfig:
    """获取专家配置"""
    return get_config_manager().get_expert_config(expert_id)