"""
数据持久化和备份系统测试
测试数据存储、备份、恢复和完整性检查功能
"""

import unittest
import tempfile
import shutil
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ..core.data_persistence_backup import (
    DataPersistenceManager, BackupType, StorageType, DataCategory,
    BackupConfig, BackupMetadata, DataIntegrityCheck,
    create_data_manager, data_persistence_decorator, async_data_persistence_decorator
)


class TestDataPersistenceManager(unittest.TestCase):
    """测试数据持久化管理器"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataPersistenceManager(self.temp_dir)
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_json_data(self):
        """测试JSON数据保存和加载"""
        test_data = {
            "name": "测试数据",
            "value": 42,
            "list": [1, 2, 3]
        }
        
        # 保存数据
        success = self.data_manager.save_data(
            test_data, "test.json", DataCategory.CONFIGURATION
        )
        self.assertTrue(success)
        
        # 加载数据
        loaded_data = self.data_manager.load_data(
            "test.json", DataCategory.CONFIGURATION
        )
        self.assertEqual(loaded_data, test_data)
    
    def test_save_and_load_pickle_data(self):
        """测试pickle数据保存和加载"""
        class TestClass:
            def __init__(self, value):
                self.value = value
            
            def get_value(self):
                return self.value
        
        test_obj = TestClass("test_value")
        
        # 保存数据
        success = self.data_manager.save_data(
            test_obj, "test.pkl", DataCategory.USER_DATA
        )
        self.assertTrue(success)
        
        # 加载数据
        loaded_obj = self.data_manager.load_data(
            "test.pkl", DataCategory.USER_DATA
        )
        self.assertEqual(loaded_obj.value, "test_value")
        self.assertEqual(loaded_obj.get_value(), "test_value")
    
    def test_nonexistent_file_loading(self):
        """测试加载不存在的文件"""
        loaded_data = self.data_manager.load_data(
            "nonexistent.json", DataCategory.CONFIGURATION
        )
        self.assertIsNone(loaded_data)
    
    def test_data_encryption(self):
        """测试数据加密"""
        # 创建带密码的数据管理器
        encrypted_manager = DataPersistenceManager(
            self.temp_dir + "_encrypted", "test_password"
        )
        
        test_data = {"secret": "sensitive_data"}
        
        # 保存加密数据
        success = encrypted_manager.save_data(
            test_data, "encrypted.json", DataCategory.CONFIGURATION, encrypt=True
        )
        self.assertTrue(success)
        
        # 加载加密数据
        loaded_data = encrypted_manager.load_data(
            "encrypted.json", DataCategory.CONFIGURATION, encrypted=True
        )
        self.assertEqual(loaded_data, test_data)
        
        # 清理
        shutil.rmtree(self.temp_dir + "_encrypted")


class TestBackupManager(unittest.TestCase):
    """测试备份管理器"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataPersistenceManager(self.temp_dir)
        
        # 创建测试数据
        self._create_test_data()
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_data(self):
        """创建测试数据"""
        # 创建配置文件
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "api": {
                "timeout": 30
            }
        }
        
        self.data_manager.save_data(
            config_data, "app_config.json", DataCategory.CONFIGURATION
        )
        
        # 创建用户数据
        user_data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        
        self.data_manager.save_data(
            user_data, "users.json", DataCategory.USER_DATA
        )
    
    def test_create_backup(self):
        """测试创建备份"""
        backup_config = BackupConfig(
            backup_type=BackupType.FULL,
            retention_days=7
        )
        
        metadata = self.data_manager.backup_manager.create_backup(
            backup_config, "测试备份"
        )
        
        self.assertIsNotNone(metadata)
        self.assertTrue(metadata.success)
        self.assertGreater(metadata.data_size, 0)
        self.assertGreater(metadata.file_count, 0)
        self.assertIsNotNone(metadata.checksum)
    
    def test_backup_restore(self):
        """测试备份恢复"""
        # 创建备份
        backup_config = BackupConfig(backup_type=BackupType.FULL)
        metadata = self.data_manager.backup_manager.create_backup(backup_config)
        
        # 删除原始数据
        shutil.rmtree(Path(self.temp_dir) / "configuration")
        shutil.rmtree(Path(self.temp_dir) / "user_data")
        
        # 恢复备份
        success = self.data_manager.backup_manager.restore_backup(metadata.backup_id)
        self.assertTrue(success)
        
        # 验证数据恢复
        config_data = self.data_manager.load_data(
            "app_config.json", DataCategory.CONFIGURATION
        )
        self.assertIsNotNone(config_data)
        self.assertEqual(config_data["database"]["host"], "localhost")
    
    def test_backup_checksum_verification(self):
        """测试备份校验和验证"""
        # 创建备份
        backup_config = BackupConfig(backup_type=BackupType.FULL)
        metadata = self.data_manager.backup_manager.create_backup(backup_config)
        
        # 篡改备份文件
        backup_dir = Path(self.temp_dir) / "backups" / metadata.backup_id
        config_file = backup_dir / "configuration" / "app_config.json"
        
        if config_file.exists():
            with open(config_file, 'w') as f:
                f.write("corrupted_data")
        
        # 尝试恢复应该失败
        success = self.data_manager.backup_manager.restore_backup(metadata.backup_id)
        self.assertFalse(success)
    
    def test_backup_cleanup(self):
        """测试备份清理"""
        # 创建多个备份
        for i in range(3):
            backup_config = BackupConfig(backup_type=BackupType.FULL)
            self.data_manager.backup_manager.create_backup(backup_config)
        
        # 获取备份数量
        initial_count = len(self.data_manager.backup_manager.backup_history)
        
        # 清理备份（模拟旧备份）
        self.data_manager.backup_manager.cleanup_old_backups(retention_days=0)
        
        # 验证备份被清理
        final_count = len(self.data_manager.backup_manager.backup_history)
        self.assertLess(final_count, initial_count)


class TestDataIntegrityChecker(unittest.TestCase):
    """测试数据完整性检查器"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataPersistenceManager(self.temp_dir)
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_integrity_check_healthy_data(self):
        """测试健康数据完整性检查"""
        # 创建健康数据
        healthy_data = {"status": "healthy"}
        self.data_manager.save_data(
            healthy_data, "healthy.json", DataCategory.CONFIGURATION
        )
        
        # 检查完整性
        integrity_check = self.data_manager.integrity_checker.check_data_integrity(
            DataCategory.CONFIGURATION
        )
        
        self.assertEqual(integrity_check.data_category, DataCategory.CONFIGURATION)
        self.assertEqual(integrity_check.file_count, 1)
        self.assertEqual(len(integrity_check.corrupted_files), 0)
        self.assertTrue(integrity_check.checksum_matches)
        self.assertEqual(integrity_check.integrity_score, 1.0)
    
    def test_integrity_check_corrupted_data(self):
        """测试损坏数据完整性检查"""
        # 创建损坏的JSON文件
        corrupted_file = Path(self.temp_dir) / "configuration" / "corrupted.json"
        corrupted_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(corrupted_file, 'w') as f:
            f.write("{invalid json")
        
        # 检查完整性
        integrity_check = self.data_manager.integrity_checker.check_data_integrity(
            DataCategory.CONFIGURATION
        )
        
        self.assertGreater(len(integrity_check.corrupted_files), 0)
        self.assertFalse(integrity_check.checksum_matches)
        self.assertLess(integrity_check.integrity_score, 1.0)
    
    def test_system_integrity_check(self):
        """测试系统完整性检查"""
        # 创建测试数据
        test_data = {"test": "data"}
        self.data_manager.save_data(
            test_data, "test1.json", DataCategory.CONFIGURATION
        )
        self.data_manager.save_data(
            test_data, "test2.json", DataCategory.USER_DATA
        )
        
        # 执行系统完整性检查
        integrity_results = self.data_manager.check_system_integrity()
        
        self.assertIn(DataCategory.CONFIGURATION, integrity_results)
        self.assertIn(DataCategory.USER_DATA, integrity_results)
        
        for category, result in integrity_results.items():
            self.assertEqual(result.data_category, category)
            self.assertGreaterEqual(result.integrity_score, 0.0)
            self.assertLessEqual(result.integrity_score, 1.0)


class TestStorageManagement(unittest.TestCase):
    """测试存储管理"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataPersistenceManager(self.temp_dir)
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_storage_usage_tracking(self):
        """测试存储使用跟踪"""
        # 创建测试数据
        large_data = {"data": "x" * 1024}  # 1KB数据
        
        for i in range(10):
            self.data_manager.save_data(
                large_data, f"large_{i}.json", DataCategory.USER_DATA
            )
        
        # 获取存储使用情况
        storage_usage = self.data_manager.storage_manager.get_storage_usage()
        
        self.assertIn(DataCategory.USER_DATA, storage_usage)
        self.assertGreater(storage_usage[DataCategory.USER_DATA], 0)
    
    def test_storage_report_generation(self):
        """测试存储报告生成"""
        # 创建测试数据
        test_data = {"report": "test"}
        self.data_manager.save_data(
            test_data, "report.json", DataCategory.CONFIGURATION
        )
        
        # 生成存储报告
        report = self.data_manager.get_storage_report()
        
        self.assertIn('timestamp', report)
        self.assertIn('total_storage_usage', report)
        self.assertIn('storage_by_category', report)
        self.assertIn('integrity_score', report)
        self.assertIn('integrity_details', report)
        self.assertIn('backup_count', report)
        
        self.assertGreaterEqual(report['integrity_score'], 0.0)
        self.assertLessEqual(report['integrity_score'], 1.0)


class TestDecorators(unittest.TestCase):
    """测试装饰器"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_data_persistence_decorator(self):
        """测试数据持久化装饰器"""
        call_count = 0
        
        @data_persistence_decorator(
            DataCategory.CONFIGURATION, "decorator_test.json"
        )
        def expensive_operation():
            nonlocal call_count
            call_count += 1
            return {"result": f"computed_{call_count}"}
        
        # 第一次调用应该执行函数
        result1 = expensive_operation()
        self.assertEqual(result1["result"], "computed_1")
        self.assertEqual(call_count, 1)
        
        # 第二次调用应该从缓存加载
        result2 = expensive_operation()
        self.assertEqual(result2["result"], "computed_1")  # 应该是缓存的结果
        self.assertEqual(call_count, 1)  # 函数不应该再次执行
    
    def test_async_data_persistence_decorator(self):
        """测试异步数据持久化装饰器"""
        import asyncio
        
        call_count = 0
        
        @async_data_persistence_decorator(
            DataCategory.USER_DATA, "async_decorator_test.json"
        )
        async def async_expensive_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return {"async_result": f"async_computed_{call_count}"}
        
        async def test_async():
            # 第一次调用应该执行函数
            result1 = await async_expensive_operation()
            self.assertEqual(result1["async_result"], "async_computed_1")
            self.assertEqual(call_count, 1)
            
            # 第二次调用应该从缓存加载
            result2 = await async_expensive_operation()
            self.assertEqual(result2["async_result"], "async_computed_1")
            self.assertEqual(call_count, 1)
        
        asyncio.run(test_async())


class TestRealWorldScenarios(unittest.TestCase):
    """测试真实场景"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataPersistenceManager(self.temp_dir)
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_configuration_management(self):
        """测试配置管理"""
        # 保存应用配置
        app_config = {
            "version": "1.0.0",
            "features": {
                "authentication": True,
                "logging": {
                    "level": "INFO",
                    "file": "app.log"
                }
            }
        }
        
        success = self.data_manager.save_data(
            app_config, "application.json", DataCategory.CONFIGURATION
        )
        self.assertTrue(success)
        
        # 加载配置
        loaded_config = self.data_manager.load_data(
            "application.json", DataCategory.CONFIGURATION
        )
        self.assertEqual(loaded_config["version"], "1.0.0")
        self.assertTrue(loaded_config["features"]["authentication"])
    
    def test_user_data_management(self):
        """测试用户数据管理"""
        # 模拟用户数据
        user_profiles = [
            {
                "id": 1,
                "username": "alice",
                "preferences": {
                    "theme": "dark",
                    "language": "zh-CN"
                }
            },
            {
                "id": 2,
                "username": "bob",
                "preferences": {
                    "theme": "light",
                    "language": "en-US"
                }
            }
        ]
        
        # 保存用户数据
        success = self.data_manager.save_data(
            user_profiles, "profiles.json", DataCategory.USER_DATA
        )
        self.assertTrue(success)
        
        # 修改用户数据
        user_profiles[0]["preferences"]["theme"] = "blue"
        success = self.data_manager.save_data(
            user_profiles, "profiles.json", DataCategory.USER_DATA
        )
        self.assertTrue(success)
        
        # 验证修改
        loaded_profiles = self.data_manager.load_data(
            "profiles.json", DataCategory.USER_DATA
        )
        self.assertEqual(loaded_profiles[0]["preferences"]["theme"], "blue")
    
    def test_disaster_recovery_scenario(self):
        """测试灾难恢复场景"""
        # 创建重要数据
        critical_data = {
            "database_connections": [
                {"name": "primary", "url": "postgresql://localhost:5432/main"},
                {"name": "replica", "url": "postgresql://localhost:5433/replica"}
            ],
            "api_keys": {
                "stripe": "sk_test_123",
                "sendgrid": "SG.abc123"
            }
        }
        
        # 保存重要数据
        self.data_manager.save_data(
            critical_data, "secrets.json", DataCategory.CONFIGURATION, encrypt=True
        )
        
        # 创建备份
        backup_metadata = self.data_manager.create_scheduled_backup("灾难恢复测试")
        self.assertIsNotNone(backup_metadata)
        
        # 模拟数据丢失
        shutil.rmtree(Path(self.temp_dir) / "configuration")
        
        # 从备份恢复
        success = self.data_manager.backup_manager.restore_backup(backup_metadata.backup_id)
        self.assertTrue(success)
        
        # 验证数据恢复
        recovered_data = self.data_manager.load_data(
            "secrets.json", DataCategory.CONFIGURATION, encrypted=True
        )
        self.assertEqual(recovered_data["api_keys"]["stripe"], "sk_test_123")


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataPersistenceManager(self.temp_dir)
    
    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_invalid_file_path_handling(self):
        """测试无效文件路径处理"""
        # 尝试使用无效路径
        success = self.data_manager.save_data(
            {"test": "data"}, "../invalid/path.json", DataCategory.CONFIGURATION
        )
        self.assertFalse(success)
    
    def test_large_file_handling(self):
        """测试大文件处理"""
        # 创建大文件数据
        large_data = {"content": "x" * (10 * 1024 * 1024)}  # 10MB数据
        
        success = self.data_manager.save_data(
            large_data, "large_file.json", DataCategory.USER_DATA
        )
        
        # 大文件应该被拒绝或处理
        # 具体行为取决于实现，这里只测试不崩溃
        self.assertIsNotNone(success)
    
    def test_corrupted_backup_handling(self):
        """测试损坏备份处理"""
        # 尝试恢复不存在的备份
        success = self.data_manager.backup_manager.restore_backup("nonexistent_backup")
        self.assertFalse(success)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)