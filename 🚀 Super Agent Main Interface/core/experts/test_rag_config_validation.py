#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG配置验证和默认值管理测试
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from .rag_config import (
    LogLevel, RAGExpertConfig, RAGSystemConfig, 
    RAGConfigManager, get_config_manager
)


def test_rag_expert_config_defaults():
    """测试专家配置默认值"""
    config = RAGExpertConfig()
    
    assert config.quality_threshold == 0.7
    assert config.high_quality_threshold == 0.8
    assert config.max_processing_time == 30.0
    assert config.batch_size == 100
    assert config.enable_monitoring is True
    assert config.log_level == "debug"


def test_rag_system_config_defaults():
    """测试系统配置默认值"""
    config = RAGSystemConfig()
    
    assert config.max_concurrent_requests == 10
    assert config.request_timeout == 60.0
    assert config.retry_attempts == 3
    assert config.cache_enabled is True
    assert config.cache_ttl == 3600
    assert config.monitoring_enabled is True


def test_config_manager_default_config():
    """测试配置管理器默认配置"""
    manager = RAGConfigManager()
    
    # 测试默认配置加载
    knowledge_config = manager.get_expert_config("knowledge")
    assert isinstance(knowledge_config, RAGExpertConfig)
    assert knowledge_config.quality_threshold == 0.85
    
    retrieval_config = manager.get_expert_config("retrieval")
    assert isinstance(retrieval_config, RAGExpertConfig)
    
    system_config = manager.load_config()
    assert isinstance(system_config, RAGSystemConfig)


def test_config_manager_environment_variables():
    """测试环境变量配置"""
    with patch.dict(os.environ, {
        "KNOWLEDGE_QUALITY_THRESHOLD": "0.8",
        "RAG_MAX_CONCURRENT_REQUESTS": "20",
        "RAG_CACHE_ENABLED": "false"
    }):
        manager = RAGConfigManager()
        
        # 测试环境变量覆盖
        knowledge_config = manager.get_expert_config("knowledge")
        assert knowledge_config.quality_threshold == 0.8
        
        system_config = manager.load_config()
        assert system_config.max_concurrent_requests == 20
        assert system_config.cache_enabled is False


def test_config_manager_file_config():
    """测试文件配置"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "experts": {
                "knowledge": {
                    "quality_threshold": 0.9,
                    "max_processing_time": 60.0
                }
            },
            "max_concurrent_requests": 50,
            "cache_ttl": 7200
        }
        json.dump(config_data, f)
        config_file = f.name
    
    try:
        with patch.dict(os.environ, {"RAG_CONFIG_PATH": config_file}):
            manager = RAGConfigManager()
            
            # 测试文件配置加载
            knowledge_config = manager.get_expert_config("knowledge")
            assert knowledge_config.quality_threshold == 0.9
            assert knowledge_config.max_processing_time == 60.0
            
            system_config = manager.load_config()
            assert system_config.max_concurrent_requests == 50
            assert system_config.cache_ttl == 7200
    
    finally:
        # 清理临时文件
        os.unlink(config_file)


def test_config_validation():
    """测试配置验证"""
    manager = RAGConfigManager()
    
    # 测试有效配置
    valid_config = RAGSystemConfig(
        max_concurrent_requests=10,
        request_timeout=60.0,
        experts={
            "knowledge": RAGExpertConfig(
                quality_threshold=0.8,
                max_processing_time=30.0
            )
        }
    )
    
    errors = manager.validate_config(valid_config)
    assert len(errors) == 0
    
    # 测试无效配置
    invalid_config = RAGSystemConfig(
        max_concurrent_requests=-10,  # 负数
        request_timeout=60.0,
        experts={
            "knowledge": RAGExpertConfig(
                quality_threshold=1.5,  # 超出范围
                max_processing_time=-10  # 负数
            )
        }
    )
    
    errors = manager.validate_config(invalid_config)
    assert len(errors) > 0


def test_config_save_load():
    """测试配置保存和加载"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "test_config.json"
        
        manager = RAGConfigManager()
        
        # 创建自定义配置
        custom_config = RAGSystemConfig(
            max_concurrent_requests=15,
            cache_ttl=1800,
            experts={
                "knowledge": RAGExpertConfig(
                    quality_threshold=0.85,
                    log_level="debug"
                )
            }
        )
        
        # 保存配置
        manager.save_config(custom_config, 'json')
        assert Path(manager.config_path).exists()
        
        # 加载配置
        loaded_config = manager.load_config()
        assert loaded_config.max_concurrent_requests == 15
        assert loaded_config.experts["knowledge"].quality_threshold == 0.85


def test_config_priority():
    """测试配置优先级（环境变量 > 配置文件 > 默认值）"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "experts": {
                "knowledge": {
                    "quality_threshold": 0.8,
                    "max_processing_time": 45.0
                }
            }
        }
        json.dump(config_data, f)
        config_file = f.name
    
    try:
        with patch.dict(os.environ, {
            "RAG_CONFIG_PATH": config_file,
            "KNOWLEDGE_QUALITY_THRESHOLD": "0.9"  # 环境变量优先级更高
        }):
            manager = RAGConfigManager()
            
            knowledge_config = manager.get_expert_config("knowledge")
            
            # 环境变量应该覆盖文件配置
            assert knowledge_config.quality_threshold == 0.9
            # 文件配置应该覆盖默认值
            assert knowledge_config.max_processing_time == 45.0
    
    finally:
        os.unlink(config_file)


def test_get_config_manager_singleton():
    """测试配置管理器单例模式"""
    manager1 = get_config_manager()
    manager2 = get_config_manager()
    
    assert manager1 is manager2


def test_config_to_from_dict():
    """测试配置对象与字典转换"""
    # 测试专家配置
    expert_config = RAGExpertConfig(
        quality_threshold=0.85,
        high_quality_threshold=0.9,
        max_processing_time=40.0,
        log_level="debug"
    )
    
    config_dict = expert_config.to_dict()
    assert config_dict["quality_threshold"] == 0.85
    assert config_dict["log_level"] == "debug"
    
    restored_config = RAGExpertConfig.from_dict(config_dict)
    assert restored_config.quality_threshold == 0.85
    assert restored_config.log_level == "debug"
    
    # 测试系统配置
    system_config = RAGSystemConfig(
        max_concurrent_requests=20,
        request_timeout=90.0,
        cache_enabled=False
    )
    
    system_dict = system_config.to_dict()
    restored_system = RAGSystemConfig.from_dict(system_dict)
    assert restored_system.max_concurrent_requests == 20
    assert restored_system.cache_enabled is False


def test_config_error_handling():
    """测试配置错误处理"""
    manager = RAGConfigManager()
    
    # 测试不存在的配置文件
    manager.config_path = "/nonexistent/config.json"
    result = manager.load_config()
    assert isinstance(result, RAGSystemConfig)
    
    # 测试无效的配置文件格式
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        invalid_config_file = f.name
    
    try:
        manager.config_path = invalid_config_file
        result = manager.load_config()
        assert isinstance(result, RAGSystemConfig)
    finally:
        os.unlink(invalid_config_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])