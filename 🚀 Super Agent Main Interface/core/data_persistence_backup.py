"""
数据持久化和备份机制
实现数据存储、备份、恢复和灾难恢复功能
"""

import os
import json
import pickle
import logging
import asyncio
import shutil
import zipfile
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import psutil
import aiofiles
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class BackupType(Enum):
    """备份类型枚举"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class StorageType(Enum):
    """存储类型枚举"""
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class DataCategory(Enum):
    """数据分类枚举"""
    CONFIGURATION = "configuration"
    USER_DATA = "user_data"
    SYSTEM_DATA = "system_data"
    LOGS = "logs"
    CACHE = "cache"
    BACKUP = "backup"


@dataclass
class BackupConfig:
    """备份配置数据类"""
    backup_type: BackupType = BackupType.FULL
    storage_type: StorageType = StorageType.LOCAL
    retention_days: int = 30
    compression: bool = True
    encryption: bool = True
    max_backup_size: int = 1024 * 1024 * 1024  # 1GB
    backup_schedule: str = "0 2 * * *"  # 每天凌晨2点
    enabled: bool = True


@dataclass
class BackupMetadata:
    """备份元数据"""
    backup_id: str
    timestamp: datetime
    backup_type: BackupType
    data_size: int
    file_count: int
    checksum: str
    encryption_key: Optional[str] = None
    description: str = ""
    success: bool = True


@dataclass
class DataIntegrityCheck:
    """数据完整性检查结果"""
    timestamp: datetime
    data_category: DataCategory
    file_count: int
    total_size: int
    corrupted_files: List[str]
    checksum_matches: bool
    integrity_score: float


class DataEncryptionManager:
    """数据加密管理器"""
    
    def __init__(self, master_password: str):
        self.master_password = master_password.encode()
        self.key_cache: Dict[str, bytes] = {}
        self.logger = logging.getLogger(__name__)
    
    def _derive_key(self, salt: bytes) -> bytes:
        """派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_password))
    
    def encrypt_data(self, data: bytes, data_id: str) -> bytes:
        """加密数据"""
        salt = os.urandom(16)
        key = self._derive_key(salt)
        
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)
        
        # 保存密钥缓存
        self.key_cache[data_id] = key
        
        return salt + encrypted_data
    
    def decrypt_data(self, encrypted_data: bytes, data_id: str) -> bytes:
        """解密数据"""
        if len(encrypted_data) < 16:
            raise ValueError("Invalid encrypted data")
        
        salt = encrypted_data[:16]
        actual_data = encrypted_data[16:]
        
        # 尝试从缓存获取密钥
        key = self.key_cache.get(data_id)
        if key is None:
            key = self._derive_key(salt)
        
        fernet = Fernet(key)
        return fernet.decrypt(actual_data)


class LocalStorageManager:
    """本地存储管理器"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def save_data(self, data: Any, file_path: str, data_category: DataCategory) -> bool:
        """保存数据到本地"""
        try:
            full_path = self.base_path / data_category.value / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(data, (dict, list)):
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                with open(full_path, 'wb') as f:
                    pickle.dump(data, f)
            
            self.logger.info(f"数据保存成功: {full_path}")
            return True
        except Exception as e:
            self.logger.error(f"数据保存失败: {e}")
            return False
    
    def load_data(self, file_path: str, data_category: DataCategory) -> Optional[Any]:
        """从本地加载数据"""
        try:
            full_path = self.base_path / data_category.value / file_path
            
            if not full_path.exists():
                return None
            
            # 尝试JSON格式
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 回退到pickle格式
                with open(full_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return None
    
    def delete_data(self, file_path: str, data_category: DataCategory) -> bool:
        """删除本地数据"""
        try:
            full_path = self.base_path / data_category.value / file_path
            
            if full_path.exists():
                full_path.unlink()
                self.logger.info(f"数据删除成功: {full_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"数据删除失败: {e}")
            return False
    
    def get_storage_usage(self) -> Dict[DataCategory, int]:
        """获取存储使用情况"""
        usage = {}
        
        for category in DataCategory:
            category_path = self.base_path / category.value
            if category_path.exists():
                total_size = sum(f.stat().st_size for f in category_path.rglob('*') if f.is_file())
                usage[category] = total_size
        
        return usage


class BackupManager:
    """备份管理器"""
    
    def __init__(self, storage_manager: LocalStorageManager, 
                 encryption_manager: Optional[DataEncryptionManager] = None):
        self.storage_manager = storage_manager
        self.encryption_manager = encryption_manager
        self.backup_history: Dict[str, BackupMetadata] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self, backup_config: BackupConfig, 
                     description: str = "") -> Optional[BackupMetadata]:
        """创建备份"""
        try:
            backup_id = self._generate_backup_id()
            timestamp = datetime.now()
            
            # 创建备份目录
            backup_dir = self.storage_manager.base_path / "backups" / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份数据
            data_size, file_count = self._backup_data(backup_dir, backup_config)
            
            # 计算校验和
            checksum = self._calculate_checksum(backup_dir)
            
            # 创建元数据
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp,
                backup_type=backup_config.backup_type,
                data_size=data_size,
                file_count=file_count,
                checksum=checksum,
                description=description
            )
            
            # 保存元数据
            self.backup_history[backup_id] = metadata
            self._save_backup_metadata(metadata)
            
            self.logger.info(f"备份创建成功: {backup_id}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"备份创建失败: {e}")
            return None
    
    def _backup_data(self, backup_dir: Path, config: BackupConfig) -> tuple[int, int]:
        """备份数据"""
        total_size = 0
        file_count = 0
        
        for category in DataCategory:
            if category == DataCategory.BACKUP:  # 跳过备份目录本身
                continue
            
            source_dir = self.storage_manager.base_path / category.value
            if not source_dir.exists():
                continue
            
            # 复制文件
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.storage_manager.base_path)
                    dest_path = backup_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(file_path, dest_path)
                    
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        return total_size, file_count
    
    def restore_backup(self, backup_id: str, target_path: Optional[str] = None) -> bool:
        """恢复备份"""
        try:
            if backup_id not in self.backup_history:
                self.logger.error(f"备份不存在: {backup_id}")
                return False
            
            backup_dir = self.storage_manager.base_path / "backups" / backup_id
            if not backup_dir.exists():
                self.logger.error(f"备份目录不存在: {backup_dir}")
                return False
            
            # 验证校验和
            current_checksum = self._calculate_checksum(backup_dir)
            if current_checksum != self.backup_history[backup_id].checksum:
                self.logger.error("备份校验和验证失败")
                return False
            
            # 恢复数据
            restore_path = Path(target_path) if target_path else self.storage_manager.base_path
            
            for file_path in backup_dir.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(backup_dir)
                    dest_path = restore_path / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(file_path, dest_path)
            
            self.logger.info(f"备份恢复成功: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"备份恢复失败: {e}")
            return False
    
    def _generate_backup_id(self) -> str:
        """生成备份ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"backup_{timestamp}_{random_suffix}"
    
    def _calculate_checksum(self, directory: Path) -> str:
        """计算目录校验和"""
        hash_md5 = hashlib.md5()
        
        for file_path in sorted(directory.rglob('*')):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """保存备份元数据"""
        metadata_file = self.storage_manager.base_path / "backups" / "metadata.json"
        
        # 加载现有元数据
        existing_metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
        
        # 更新元数据
        existing_metadata[metadata.backup_id] = {
            'timestamp': metadata.timestamp.isoformat(),
            'backup_type': metadata.backup_type.value,
            'data_size': metadata.data_size,
            'file_count': metadata.file_count,
            'checksum': metadata.checksum,
            'description': metadata.description,
            'success': metadata.success
        }
        
        # 保存元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(existing_metadata, f, indent=2, ensure_ascii=False)
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """清理旧备份"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            backups_dir = self.storage_manager.base_path / "backups"
            if not backups_dir.exists():
                return
            
            for backup_dir in backups_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                    # 从目录名解析时间
                    try:
                        dir_date_str = backup_dir.name.split('_')[1]
                        dir_date = datetime.strptime(dir_date_str, "%Y%m%d")
                        
                        if dir_date < cutoff_date:
                            shutil.rmtree(backup_dir)
                            self.logger.info(f"删除旧备份: {backup_dir.name}")
                    except (ValueError, IndexError):
                        continue
            
        except Exception as e:
            self.logger.error(f"备份清理失败: {e}")


class DataIntegrityChecker:
    """数据完整性检查器"""
    
    def __init__(self, storage_manager: LocalStorageManager):
        self.storage_manager = storage_manager
        self.logger = logging.getLogger(__name__)
    
    def check_data_integrity(self, data_category: DataCategory) -> DataIntegrityCheck:
        """检查数据完整性"""
        timestamp = datetime.now()
        corrupted_files = []
        total_size = 0
        file_count = 0
        
        category_path = self.storage_manager.base_path / data_category.value
        
        if not category_path.exists():
            return DataIntegrityCheck(
                timestamp=timestamp,
                data_category=data_category,
                file_count=0,
                total_size=0,
                corrupted_files=[],
                checksum_matches=True,
                integrity_score=1.0
            )
        
        # 检查文件完整性
        for file_path in category_path.rglob('*'):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
                
                if not self._verify_file_integrity(file_path):
                    corrupted_files.append(str(file_path))
        
        # 计算完整性分数
        integrity_score = 1.0 - (len(corrupted_files) / max(file_count, 1))
        
        return DataIntegrityCheck(
            timestamp=timestamp,
            data_category=data_category,
            file_count=file_count,
            total_size=total_size,
            corrupted_files=corrupted_files,
            checksum_matches=len(corrupted_files) == 0,
            integrity_score=integrity_score
        )
    
    def _verify_file_integrity(self, file_path: Path) -> bool:
        """验证文件完整性"""
        try:
            # 尝试读取文件
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            else:
                with open(file_path, 'rb') as f:
                    pickle.load(f)
            
            # 检查文件大小是否合理
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB限制
                self.logger.warning(f"文件过大: {file_path}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"文件完整性检查失败 {file_path}: {e}")
            return False


class DataPersistenceManager:
    """数据持久化管理器"""
    
    def __init__(self, base_storage_path: str, master_password: Optional[str] = None):
        self.storage_manager = LocalStorageManager(base_storage_path)
        
        if master_password:
            self.encryption_manager = DataEncryptionManager(master_password)
        else:
            self.encryption_manager = None
        
        self.backup_manager = BackupManager(self.storage_manager, self.encryption_manager)
        self.integrity_checker = DataIntegrityChecker(self.storage_manager)
        
        self.logger = logging.getLogger(__name__)
        self._setup_default_backup_config()
    
    def _setup_default_backup_config(self):
        """设置默认备份配置"""
        self.default_backup_config = BackupConfig(
            backup_type=BackupType.FULL,
            storage_type=StorageType.LOCAL,
            retention_days=30,
            compression=True,
            encryption=True,
            max_backup_size=1024 * 1024 * 1024,
            backup_schedule="0 2 * * *",
            enabled=True
        )
    
    def save_data(self, data: Any, file_path: str, 
                 data_category: DataCategory, encrypt: bool = False) -> bool:
        """保存数据"""
        try:
            # 加密数据
            if encrypt and self.encryption_manager:
                if isinstance(data, (dict, list)):
                    data_bytes = json.dumps(data).encode('utf-8')
                else:
                    data_bytes = pickle.dumps(data)
                
                encrypted_data = self.encryption_manager.encrypt_data(data_bytes, file_path)
                return self.storage_manager.save_data(encrypted_data, file_path, data_category)
            else:
                return self.storage_manager.save_data(data, file_path, data_category)
        except Exception as e:
            self.logger.error(f"数据保存失败: {e}")
            return False
    
    def load_data(self, file_path: str, data_category: DataCategory, 
                 encrypted: bool = False) -> Optional[Any]:
        """加载数据"""
        try:
            data = self.storage_manager.load_data(file_path, data_category)
            
            if data is None:
                return None
            
            # 解密数据
            if encrypted and self.encryption_manager:
                if isinstance(data, bytes):
                    decrypted_bytes = self.encryption_manager.decrypt_data(data, file_path)
                    
                    # 尝试解析为JSON或pickle
                    try:
                        return json.loads(decrypted_bytes.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        return pickle.loads(decrypted_bytes)
            
            return data
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return None
    
    def create_scheduled_backup(self, description: str = "") -> Optional[BackupMetadata]:
        """创建定时备份"""
        return self.backup_manager.create_backup(self.default_backup_config, description)
    
    def check_system_integrity(self) -> Dict[DataCategory, DataIntegrityCheck]:
        """检查系统完整性"""
        results = {}
        
        for category in DataCategory:
            if category != DataCategory.BACKUP:  # 跳过备份目录
                results[category] = self.integrity_checker.check_data_integrity(category)
        
        return results
    
    def get_storage_report(self) -> Dict[str, Any]:
        """获取存储报告"""
        storage_usage = self.storage_manager.get_storage_usage()
        integrity_results = self.check_system_integrity()
        
        total_size = sum(storage_usage.values())
        integrity_score = statistics.mean([
            result.integrity_score for result in integrity_results.values()
        ]) if integrity_results else 1.0
        
        return {
            'timestamp': datetime.now(),
            'total_storage_usage': total_size,
            'storage_by_category': {cat.value: size for cat, size in storage_usage.items()},
            'integrity_score': integrity_score,
            'integrity_details': {
                cat.value: {
                    'file_count': result.file_count,
                    'corrupted_files': len(result.corrupted_files),
                    'integrity_score': result.integrity_score
                }
                for cat, result in integrity_results.items()
            },
            'backup_count': len(self.backup_manager.backup_history)
        }
    
    def cleanup_system(self, cleanup_config: Dict[DataCategory, bool]):
        """清理系统"""
        try:
            for category, should_cleanup in cleanup_config.items():
                if should_cleanup:
                    category_path = self.storage_manager.base_path / category.value
                    if category_path.exists():
                        shutil.rmtree(category_path)
                        self.logger.info(f"清理数据类别: {category.value}")
        except Exception as e:
            self.logger.error(f"系统清理失败: {e}")


# 全局数据持久化管理器实例
def create_data_manager(base_path: str = "data", master_password: Optional[str] = None):
    """创建数据管理器实例"""
    return DataPersistenceManager(base_path, master_password)


def data_persistence_decorator(data_category: DataCategory, 
                             file_path: str, encrypt: bool = False):
    """数据持久化装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从缓存加载
            data_manager = create_data_manager()
            cached_data = data_manager.load_data(file_path, data_category, encrypt)
            
            if cached_data is not None:
                return cached_data
            
            # 执行函数获取数据
            result = func(*args, **kwargs)
            
            # 保存数据
            data_manager.save_data(result, file_path, data_category, encrypt)
            
            return result
        
        return wrapper
    
    return decorator


def async_data_persistence_decorator(data_category: DataCategory, 
                                   file_path: str, encrypt: bool = False):
    """异步数据持久化装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 尝试从缓存加载
            data_manager = create_data_manager()
            cached_data = data_manager.load_data(file_path, data_category, encrypt)
            
            if cached_data is not None:
                return cached_data
            
            # 执行函数获取数据
            result = await func(*args, **kwargs)
            
            # 保存数据
            data_manager.save_data(result, file_path, data_category, encrypt)
            
            return result
        
        return wrapper
    
    return decorator