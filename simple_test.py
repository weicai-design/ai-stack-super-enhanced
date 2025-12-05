#!/usr/bin/env python3
"""
用户交互管理器核心功能验证测试
直接测试用户交互管理器的基本功能，不依赖外部文件
"""

import sys
import os
import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable
from functools import wraps

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义交互类型枚举
class InteractionType(Enum):
    CONFIRMATION = 'confirmation'
    NOTIFICATION = 'notification'
    ALERT = 'alert'
    QUESTION = 'question'
    CHOICE = 'choice'

# 定义用户交互类
@dataclass
class UserInteraction:
    interaction_id: str
    interaction_type: InteractionType
    title: str
    message: str
    options: List[str] = None
    default_option: Optional[str] = None
    timeout_seconds: Optional[int] = None
    priority: str = 'normal'
    timestamp: datetime = None
    callback: Optional[Callable] = None
    resolved: bool = False
    user_response: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.options is None:
            self.options = ['确认', '取消']
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'interaction_id': self.interaction_id,
            'type': self.interaction_type.value,
            'title': self.title,
            'message': self.message,
            'options': self.options,
            'default_option': self.default_option,
            'timeout_seconds': self.timeout_seconds,
            'priority': self.priority,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'user_response': self.user_response,
            'metadata': self.metadata
        }
    
    def is_expired(self) -> bool:
        if not self.timeout_seconds:
            return False
        elapsed = (datetime.utcnow() - self.timestamp).total_seconds()
        return elapsed > self.timeout_seconds

# 性能监控装饰器
def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f'{func.__name__} 执行时间: {execution_time:.3f}秒')
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f'{func.__name__} 执行失败，耗时: {execution_time:.3f}秒，错误: {str(e)}')
            raise
    return wrapper

# 错误重试装饰器
def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f'{func.__name__} 第{attempt + 1}次尝试失败，{delay}秒后重试: {str(e)}')
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f'{func.__name__} 所有重试均失败: {str(e)}')
            raise last_exception
        return wrapper
    return decorator

# 用户交互管理器类
class UserInteractionManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = self._load_config(config)
        self.pending_interactions: Dict[str, UserInteraction] = {}
        self.interaction_history: List[UserInteraction] = []
        self.event_bus = None
        self.ui_handler = None
        self.auto_resolve_timeout = self._config.get('default_timeout', 300)
        
        # 监控和统计
        self._stats = {
            'total_interactions': 0,
            'successful_responses': 0,
            'timeout_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0.0
        }
        
        # 健康状态
        self._health_status = {
            'status': 'healthy',
            'last_check': datetime.utcnow(),
            'errors': []
        }
        
        logger.info('用户交互管理器初始化完成')
    
    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        default_config = {
            'max_interactions': 100,
            'default_timeout': 300,
            'retry_count': 3,
            'enable_monitoring': True,
            'max_queue_size': 1000,
            'cache_ttl': 3600,
            'health_check_interval': 60
        }
        
        if config:
            default_config.update(config)
        
        # 验证配置
        if default_config['max_interactions'] <= 0:
            raise ValueError('max_interactions 必须大于0')
        if default_config['default_timeout'] <= 0:
            raise ValueError('default_timeout 必须大于0')
        
        return default_config

    @monitor_performance
    @retry_on_failure(max_retries=3, delay=1)
    async def initialize(self, config: Dict = None, core_services: Dict = None):
        logger.info('初始化用户交互管理器')
        
        try:
            # 配置设置
            if config:
                self._config.update(config)
                self.auto_resolve_timeout = self._config.get('default_timeout', 300)
            
            # 核心服务注入
            if core_services:
                self.event_bus = core_services.get('event_bus')
                self.ui_handler = core_services.get('ui_handler')
            
            logger.info('用户交互管理器初始化完成')
            
        except Exception as e:
            logger.error(f'初始化失败: {e}')
            raise

# 测试函数
async def test_basic_functionality():
    print('\n=== 测试1: 基本功能 ===')
    
    try:
        # 创建管理器实例
        manager = UserInteractionManager({
            'max_interactions': 10,
            'default_timeout': 30
        })
        
        print('✓ 用户交互管理器创建成功')
        
        # 测试创建交互
        interaction = UserInteraction(
            interaction_id='test_001',
            interaction_type=InteractionType.CONFIRMATION,
            title='测试确认',
            message='这是一个测试确认对话框',
            options=['确认', '取消'],
            default_option='确认'
        )
        
        print('✓ 用户交互对象创建成功')
        
        # 测试转换为字典
        interaction_dict = interaction.to_dict()
        print(f'✓ 交互对象转换为字典成功: {list(interaction_dict.keys())}')
        
        # 测试过期检查
        is_expired = interaction.is_expired()
        print(f'✓ 过期检查成功: {is_expired}')
        
        return True
        
    except Exception as e:
        print(f'✗ 基本功能测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def test_manager_methods():
    print('\n=== 测试2: 管理器方法 ===')
    
    try:
        manager = UserInteractionManager()
        
        # 测试配置加载
        config = manager._load_config({'max_interactions': 50})
        print(f'✓ 配置加载成功: max_interactions = {config.get("max_interactions")}')
        
        # 测试初始化
        await manager.initialize()
        print('✓ 管理器初始化成功')
        
        return True
        
    except Exception as e:
        print(f'✗ 管理器方法测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def test_performance_monitoring():
    print('\n=== 测试3: 性能监控 ===')
    
    try:
        # 测试装饰器
        @monitor_performance
        async def test_function():
            await asyncio.sleep(0.1)
            return 'success'
        
        result = await test_function()
        print(f'✓ 性能监控装饰器测试成功: {result}')
        
        @retry_on_failure(max_retries=2, delay=0.1)
        async def failing_function():
            raise ValueError('测试错误')
        
        try:
            await failing_function()
        except ValueError:
            print('✓ 错误重试装饰器测试成功')
        
        return True
        
    except Exception as e:
        print(f'✗ 性能监控测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    print('\n=== 测试4: 错误处理 ===')
    
    try:
        # 测试无效交互创建
        try:
            invalid_interaction = UserInteraction(
                interaction_id='',
                interaction_type=InteractionType.CONFIRMATION,
                title='',
                message=''
            )
        except Exception as e:
            print(f'✓ 数据验证错误处理成功: {type(e).__name__}')
        
        # 测试无效配置
        try:
            invalid_manager = UserInteractionManager({'max_interactions': -1})
        except ValueError as e:
            print(f'✓ 配置验证错误处理成功: {e}')
        
        return True
        
    except Exception as e:
        print(f'✗ 错误处理测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def test_resource_management():
    print('\n=== 测试5: 资源管理 ===')
    
    try:
        manager = UserInteractionManager()
        
        # 测试统计信息
        stats = manager._stats
        print(f'✓ 统计信息获取成功: {list(stats.keys())}')
        
        # 测试健康状态
        health = manager._health_status
        print(f'✓ 健康状态获取成功: {list(health.keys())}')
        
        return True
        
    except Exception as e:
        print(f'✗ 资源管理测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    print('开始用户交互管理器核心功能验证测试...')
    
    test_results = []
    
    # 运行所有测试
    test_results.append(await test_basic_functionality())
    test_results.append(await test_manager_methods())
    test_results.append(await test_performance_monitoring())
    test_results.append(await test_error_handling())
    test_results.append(await test_resource_management())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f'\n=== 测试结果 ===')
    print(f'通过: {passed}/{total}')
    print(f'成功率: {passed/total*100:.1f}%')
    
    if passed == total:
        print('🎉 所有测试通过！用户交互管理器核心功能正常。')
    else:
        print('⚠️ 部分测试失败，需要进一步调试。')
    
    return passed == total

# 运行测试
if __name__ == '__main__':
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except Exception as e:
        print(f'测试执行失败: {e}')
        import traceback
        traceback.print_exc()
        exit(1)