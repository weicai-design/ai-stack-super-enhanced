#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API凭证管理器（生产级增强版）
P2-304: 提供统一的API凭证管理
4.4: 扩展功能 - Fernet加密存储、密钥轮换、审计日志
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet, MultiFernet
import hashlib
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """审计操作类型"""
    CREATE = "create"  # 创建凭证
    READ = "read"  # 读取凭证
    UPDATE = "update"  # 更新凭证
    DELETE = "delete"  # 删除凭证
    ROTATE_KEY = "rotate_key"  # 密钥轮换
    VALIDATE = "validate"  # 验证凭证
    EXPORT = "export"  # 导出凭证
    IMPORT = "import"  # 导入凭证


class APICredentialManager:
    """
    API凭证管理器
    
    功能：
    1. 统一管理所有外部API凭证
    2. 支持加密存储
    3. 支持环境变量和配置文件
    4. 凭证验证和刷新
    """
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        encrypt: bool = True,
        enable_audit: bool = True,
        key_rotation_days: int = 90,  # 密钥轮换周期（天）
    ):
        """
        初始化凭证管理器
        
        Args:
            config_dir: 配置目录（默认：项目根目录/.credentials）
            encrypt: 是否加密存储
            enable_audit: 是否启用审计日志
            key_rotation_days: 密钥轮换周期（天）
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent.parent.parent / ".credentials"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.encrypt = encrypt
        self.enable_audit = enable_audit
        self.key_rotation_days = key_rotation_days
        
        # 审计日志目录
        self.audit_dir = self.config_dir / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # 密钥管理（支持多密钥版本）
        self.key_versions: List[Dict[str, Any]] = []
        self.current_key_version = 1
        self._load_key_versions()
        
        # 加密密钥（从环境变量获取或生成）
        self.encryption_key = self._get_current_encryption_key()
        if self.encryption_key:
            self.cipher = self._create_cipher()
        else:
            self.cipher = None
        
        # 凭证缓存
        self.credentials_cache: Dict[str, Dict[str, Any]] = {}
        
        # 线程锁（用于并发安全）
        self._lock = threading.RLock()
        
        # 审计日志锁
        self._audit_lock = threading.RLock()
        
        logger.info(f"API凭证管理器初始化完成，配置目录: {self.config_dir}, 审计: {enable_audit}, 密钥轮换周期: {key_rotation_days}天")
    
    def _load_key_versions(self):
        """加载密钥版本信息"""
        key_versions_file = self.config_dir / ".key_versions.json"
        if key_versions_file.exists():
            try:
                with open(key_versions_file, 'r') as f:
                    data = json.load(f)
                    self.key_versions = data.get("versions", [])
                    self.current_key_version = data.get("current_version", 1)
            except Exception as e:
                logger.warning(f"加载密钥版本信息失败: {e}")
                self.key_versions = []
                self.current_key_version = 1
        else:
            self.key_versions = []
            self.current_key_version = 1
    
    def _save_key_versions(self):
        """保存密钥版本信息"""
        key_versions_file = self.config_dir / ".key_versions.json"
        try:
            data = {
                "versions": self.key_versions,
                "current_version": self.current_key_version,
                "updated_at": datetime.utcnow().isoformat(),
            }
            with open(key_versions_file, 'w') as f:
                json.dump(data, f, indent=2)
            key_versions_file.chmod(0o600)
        except Exception as e:
            logger.error(f"保存密钥版本信息失败: {e}")
    
    def _get_current_encryption_key(self) -> Optional[bytes]:
        """获取当前加密密钥"""
        # 从环境变量获取（优先级最高）
        key = os.getenv("API_CREDENTIAL_ENCRYPTION_KEY")
        if key:
            try:
                return key.encode()
            except:
                pass
        
        # 从密钥版本文件获取当前密钥
        if self.key_versions:
            current_key_info = next(
                (kv for kv in self.key_versions if kv.get("version") == self.current_key_version),
                None
            )
            if current_key_info:
                key_file = self.config_dir / current_key_info["key_file"]
                if key_file.exists():
                    try:
                        return key_file.read_bytes()
                    except Exception as e:
                        logger.warning(f"读取密钥文件失败: {e}")
        
        # 从旧文件获取（向后兼容）
        key_file = self.config_dir / ".encryption_key"
        if key_file.exists():
            try:
                key_bytes = key_file.read_bytes()
                # 迁移到新版本系统
                self._migrate_old_key(key_bytes)
                return key_bytes
            except Exception as e:
                logger.warning(f"读取旧密钥文件失败: {e}")
        
        # 生成新密钥
        if self.encrypt:
            return self._generate_new_key()
        
        return None
    
    def _generate_new_key(self) -> Optional[bytes]:
        """生成新密钥"""
        try:
            new_key = Fernet.generate_key()
            version = len(self.key_versions) + 1
            
            # 保存密钥文件
            key_file = self.config_dir / f".encryption_key_v{version}"
            key_file.write_bytes(new_key)
            key_file.chmod(0o600)
            
            # 记录密钥版本信息
            key_info = {
                "version": version,
                "key_file": f".encryption_key_v{version}",
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True,
            }
            self.key_versions.append(key_info)
            self.current_key_version = version
            self._save_key_versions()
            
            logger.info(f"已生成新的加密密钥（版本 {version}）")
            
            # 记录审计日志
            self._audit_log(
                AuditAction.ROTATE_KEY,
                "system",
                "key",
                metadata={"version": version, "action": "generate"}
            )
            
            return new_key
        except Exception as e:
            logger.error(f"生成新密钥失败: {e}")
            return None
    
    def _migrate_old_key(self, old_key: bytes):
        """迁移旧密钥到新版本系统"""
        try:
            if not self.key_versions:
                version = 1
                key_file = self.config_dir / ".encryption_key_v1"
                key_file.write_bytes(old_key)
                key_file.chmod(0o600)
                
                key_info = {
                    "version": 1,
                    "key_file": ".encryption_key_v1",
                    "created_at": datetime.utcnow().isoformat(),
                    "is_active": True,
                    "migrated": True,
                }
                self.key_versions.append(key_info)
                self.current_key_version = 1
                self._save_key_versions()
                
                logger.info("已迁移旧密钥到新版本系统")
        except Exception as e:
            logger.warning(f"迁移旧密钥失败: {e}")
    
    def _create_cipher(self) -> Optional[Fernet]:
        """创建加密器（支持多密钥版本）"""
        if not self.encryption_key:
            return None
        
        try:
            # 如果有多密钥版本，使用MultiFernet支持向后兼容
            if len(self.key_versions) > 1:
                keys = []
                for key_info in sorted(self.key_versions, key=lambda x: x.get("version", 0), reverse=True):
                    key_file = self.config_dir / key_info["key_file"]
                    if key_file.exists():
                        try:
                            keys.append(key_file.read_bytes())
                        except Exception as e:
                            logger.warning(f"读取密钥版本 {key_info['version']} 失败: {e}")
                
                if keys:
                    return MultiFernet([Fernet(k) for k in keys])
            
            # 单密钥版本
            return Fernet(self.encryption_key)
        except Exception as e:
            logger.error(f"创建加密器失败: {e}")
            return None
    
    def _encrypt_value(self, value: str) -> str:
        """加密值（使用当前密钥）"""
        if not self.cipher or not self.encrypt:
            return value
        try:
            encrypted = self.cipher.encrypt(value.encode())
            # 添加版本标识（如果使用MultiFernet）
            if isinstance(self.cipher, MultiFernet):
                # MultiFernet会自动使用第一个密钥（最新的）
                return encrypted.decode()
            return encrypted.decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return value
    
    def _decrypt_value(self, value: str) -> str:
        """解密值（支持多密钥版本向后兼容）"""
        if not self.cipher or not self.encrypt:
            return value
        try:
            # MultiFernet会自动尝试所有密钥
            return self.cipher.decrypt(value.encode()).decode()
        except Exception as e:
            logger.warning(f"解密失败（尝试旧密钥）: {e}")
            # 尝试使用旧密钥解密
            return self._decrypt_with_old_keys(value)
    
    def _decrypt_with_old_keys(self, value: str) -> str:
        """使用旧密钥尝试解密"""
        if not self.key_versions or len(self.key_versions) <= 1:
            raise ValueError("无法解密：没有可用的旧密钥")
        
        # 按版本倒序尝试
        for key_info in sorted(self.key_versions, key=lambda x: x.get("version", 0), reverse=True):
            if key_info.get("version") == self.current_key_version:
                continue  # 跳过当前密钥（已经尝试过）
            
            key_file = self.config_dir / key_info["key_file"]
            if key_file.exists():
                try:
                    old_key = key_file.read_bytes()
                    old_cipher = Fernet(old_key)
                    decrypted = old_cipher.decrypt(value.encode()).decode()
                    logger.info(f"使用旧密钥版本 {key_info['version']} 成功解密")
                    return decrypted
                except Exception:
                    continue
        
        raise ValueError("无法解密：所有密钥版本都失败")
    
    def _audit_log(
        self,
        action: AuditAction,
        platform: str,
        credential_type: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录审计日志"""
        if not self.enable_audit:
            return
        
        try:
            with self._audit_lock:
                audit_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": action.value,
                    "platform": platform,
                    "credential_type": credential_type,
                    "success": success,
                    "error": error,
                    "metadata": metadata or {},
                    "key_version": self.current_key_version,
                }
                
                # 写入审计日志文件（按日期）
                today = datetime.utcnow().strftime("%Y%m%d")
                audit_file = self.audit_dir / f"audit_{today}.jsonl"
                
                with open(audit_file, 'a') as f:
                    f.write(json.dumps(audit_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e}")
    
    def set_credential(
        self,
        platform: str,
        credential_type: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        设置凭证
        
        Args:
            platform: 平台名称（douyin/ths123/erp/content等）
            credential_type: 凭证类型（api_key/access_token/app_secret等）
            value: 凭证值
            metadata: 元数据（过期时间、刷新token等）
            
        Returns:
            是否成功
        """
        with self._lock:
            try:
                # 检查是否已存在（用于判断是创建还是更新）
                existing = self.get_credential(platform, credential_type)
                action = AuditAction.CREATE if not existing else AuditAction.UPDATE
                
                # 从环境变量优先
                env_key = f"{platform.upper()}_{credential_type.upper()}"
                if os.getenv(env_key):
                    logger.info(f"使用环境变量: {env_key}")
                    self.credentials_cache[platform] = self.credentials_cache.get(platform, {})
                    self.credentials_cache[platform][credential_type] = os.getenv(env_key)
                    self._audit_log(action, platform, credential_type, success=True, metadata={"source": "env"})
                    return True
                
                # 保存到文件
                cred_file = self.config_dir / f"{platform}.json"
                credentials = {}
                
                if cred_file.exists():
                    try:
                        content = cred_file.read_text()
                        credentials = json.loads(content)
                    except:
                        pass
                
                # 更新凭证
                if credential_type not in credentials:
                    credentials[credential_type] = {}
                
                credentials[credential_type]["value"] = self._encrypt_value(value)
                credentials[credential_type]["updated_at"] = datetime.utcnow().isoformat()
                credentials[credential_type]["key_version"] = self.current_key_version  # 记录使用的密钥版本
                
                if metadata:
                    credentials[credential_type]["metadata"] = metadata
                
                # 保存到文件
                cred_file.write_text(json.dumps(credentials, indent=2, ensure_ascii=False))
                cred_file.chmod(0o600)  # 仅所有者可读写
                
                # 更新缓存
                self.credentials_cache[platform] = self.credentials_cache.get(platform, {})
                self.credentials_cache[platform][credential_type] = value
                
                logger.info(f"已保存凭证: {platform}.{credential_type}")
                
                # 记录审计日志
                self._audit_log(
                    action,
                    platform,
                    credential_type,
                    success=True,
                    metadata={"key_version": self.current_key_version}
                )
                
                return True
                
            except Exception as e:
                logger.error(f"保存凭证失败: {e}", exc_info=True)
                self._audit_log(
                    AuditAction.UPDATE if existing else AuditAction.CREATE,
                    platform,
                    credential_type,
                    success=False,
                    error=str(e)
                )
                return False
    
    def get_credential(
        self,
        platform: str,
        credential_type: str,
        default: Optional[str] = None,
        audit: bool = True,
    ) -> Optional[str]:
        """
        获取凭证
        
        Args:
            platform: 平台名称
            credential_type: 凭证类型
            default: 默认值
            audit: 是否记录审计日志（默认True）
            
        Returns:
            凭证值
        """
        with self._lock:
            # 1. 从缓存获取
            if platform in self.credentials_cache:
                if credential_type in self.credentials_cache[platform]:
                    if audit:
                        self._audit_log(AuditAction.READ, platform, credential_type, success=True, metadata={"source": "cache"})
                    return self.credentials_cache[platform][credential_type]
            
            # 2. 从环境变量获取
            env_key = f"{platform.upper()}_{credential_type.upper()}"
            env_value = os.getenv(env_key)
            if env_value:
                self.credentials_cache[platform] = self.credentials_cache.get(platform, {})
                self.credentials_cache[platform][credential_type] = env_value
                if audit:
                    self._audit_log(AuditAction.READ, platform, credential_type, success=True, metadata={"source": "env"})
                return env_value
            
            # 3. 从文件获取
            cred_file = self.config_dir / f"{platform}.json"
            if cred_file.exists():
                try:
                    content = cred_file.read_text()
                    credentials = json.loads(content)
                    
                    if credential_type in credentials:
                        encrypted_value = credentials[credential_type].get("value")
                        if encrypted_value:
                            value = self._decrypt_value(encrypted_value)
                            # 更新缓存
                            self.credentials_cache[platform] = self.credentials_cache.get(platform, {})
                            self.credentials_cache[platform][credential_type] = value
                            if audit:
                                key_version = credentials[credential_type].get("key_version", "unknown")
                                self._audit_log(AuditAction.READ, platform, credential_type, success=True, metadata={"source": "file", "key_version": key_version})
                            return value
                except Exception as e:
                    logger.error(f"读取凭证失败: {e}")
                    if audit:
                        self._audit_log(AuditAction.READ, platform, credential_type, success=False, error=str(e))
            
            if audit:
                self._audit_log(AuditAction.READ, platform, credential_type, success=False, error="凭证不存在")
            
            return default
    
    def get_all_credentials(self, platform: str) -> Dict[str, Any]:
        """获取平台所有凭证"""
        credentials = {}
        
        # 从文件读取
        cred_file = self.config_dir / f"{platform}.json"
        if cred_file.exists():
            try:
                content = cred_file.read_text()
                file_creds = json.loads(content)
                for cred_type, cred_data in file_creds.items():
                    if isinstance(cred_data, dict) and "value" in cred_data:
                        credentials[cred_type] = self._decrypt_value(cred_data["value"])
                    else:
                        credentials[cred_type] = cred_data
            except Exception as e:
                logger.error(f"读取凭证失败: {e}")
        
        # 从环境变量补充
        env_prefix = f"{platform.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                cred_type = key[len(env_prefix):].lower()
                credentials[cred_type] = value
        
        return credentials
    
    def delete_credential(self, platform: str, credential_type: str) -> bool:
        """删除凭证"""
        with self._lock:
            try:
                cred_file = self.config_dir / f"{platform}.json"
                if cred_file.exists():
                    credentials = json.loads(cred_file.read_text())
                    if credential_type in credentials:
                        del credentials[credential_type]
                        cred_file.write_text(json.dumps(credentials, indent=2, ensure_ascii=False))
                
                # 清除缓存
                if platform in self.credentials_cache:
                    if credential_type in self.credentials_cache[platform]:
                        del self.credentials_cache[platform][credential_type]
                
                logger.info(f"已删除凭证: {platform}.{credential_type}")
                
                # 记录审计日志
                self._audit_log(AuditAction.DELETE, platform, credential_type, success=True)
                
                return True
                
            except Exception as e:
                logger.error(f"删除凭证失败: {e}")
                self._audit_log(AuditAction.DELETE, platform, credential_type, success=False, error=str(e))
                return False
    
    def validate_credential(self, platform: str, credential_type: str) -> bool:
        """验证凭证是否有效"""
        value = self.get_credential(platform, credential_type, audit=False)
        if not value:
            self._audit_log(AuditAction.VALIDATE, platform, credential_type, success=False, error="凭证不存在")
            return False
        
        # 基本验证（非空）
        if not value or len(value.strip()) == 0:
            self._audit_log(AuditAction.VALIDATE, platform, credential_type, success=False, error="凭证为空")
            return False
        
        # 可以添加更多验证逻辑（如格式检查、API测试等）
        self._audit_log(AuditAction.VALIDATE, platform, credential_type, success=True)
        return True
    
    # ============ 密钥轮换功能 ============
    
    def rotate_encryption_key(self, force: bool = False) -> bool:
        """
        轮换加密密钥
        
        Args:
            force: 是否强制轮换（即使未到轮换周期）
            
        Returns:
            是否成功
        """
        with self._lock:
            try:
                # 检查是否需要轮换
                if not force:
                    if self.key_versions:
                        latest_key = max(self.key_versions, key=lambda x: x.get("version", 0))
                        created_at = datetime.fromisoformat(latest_key.get("created_at", datetime.utcnow().isoformat()))
                        days_since_rotation = (datetime.utcnow() - created_at).days
                        
                        if days_since_rotation < self.key_rotation_days:
                            logger.info(f"密钥轮换周期未到（{days_since_rotation}/{self.key_rotation_days}天）")
                            return False
                
                # 生成新密钥
                new_key = self._generate_new_key()
                if not new_key:
                    return False
                
                # 重新加密所有凭证（使用新密钥）
                self._reencrypt_all_credentials()
                
                # 记录审计日志
                self._audit_log(
                    AuditAction.ROTATE_KEY,
                    "system",
                    "encryption_key",
                    success=True,
                    metadata={"new_version": self.current_key_version}
                )
                
                logger.info(f"密钥轮换完成，新版本: {self.current_key_version}")
                return True
                
            except Exception as e:
                logger.error(f"密钥轮换失败: {e}", exc_info=True)
                self._audit_log(
                    AuditAction.ROTATE_KEY,
                    "system",
                    "encryption_key",
                    success=False,
                    error=str(e)
                )
                return False
    
    def _reencrypt_all_credentials(self):
        """使用新密钥重新加密所有凭证"""
        try:
            for cred_file in self.config_dir.glob("*.json"):
                if cred_file.name.startswith("."):
                    continue
                
                try:
                    credentials = json.loads(cred_file.read_text())
                    updated = False
                    
                    for cred_type, cred_data in credentials.items():
                        if isinstance(cred_data, dict) and "value" in cred_data:
                            # 解密旧值
                            old_value = self._decrypt_value(cred_data["value"])
                            # 使用新密钥加密
                            cred_data["value"] = self._encrypt_value(old_value)
                            cred_data["key_version"] = self.current_key_version
                            cred_data["updated_at"] = datetime.utcnow().isoformat()
                            updated = True
                    
                    if updated:
                        cred_file.write_text(json.dumps(credentials, indent=2, ensure_ascii=False))
                        logger.debug(f"已重新加密凭证文件: {cred_file.name}")
                        
                except Exception as e:
                    logger.warning(f"重新加密凭证文件失败 {cred_file.name}: {e}")
                    
        except Exception as e:
            logger.error(f"重新加密所有凭证失败: {e}")
    
    def get_key_rotation_status(self) -> Dict[str, Any]:
        """获取密钥轮换状态"""
        if not self.key_versions:
            return {
                "has_keys": False,
                "current_version": 0,
                "total_versions": 0,
                "days_until_rotation": None,
            }
        
        latest_key = max(self.key_versions, key=lambda x: x.get("version", 0))
        created_at = datetime.fromisoformat(latest_key.get("created_at", datetime.utcnow().isoformat()))
        days_since_rotation = (datetime.utcnow() - created_at).days
        days_until_rotation = max(0, self.key_rotation_days - days_since_rotation)
        
        return {
            "has_keys": True,
            "current_version": self.current_key_version,
            "total_versions": len(self.key_versions),
            "latest_key_created": latest_key.get("created_at"),
            "days_since_rotation": days_since_rotation,
            "rotation_period_days": self.key_rotation_days,
            "days_until_rotation": days_until_rotation,
            "needs_rotation": days_until_rotation == 0,
        }
    
    # ============ 审计日志查询功能 ============
    
    def get_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        platform: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        获取审计日志
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            platform: 平台过滤
            action: 操作类型过滤
            limit: 最大返回数量
            
        Returns:
            审计日志列表
        """
        logs = []
        
        try:
            # 确定查询日期范围
            if start_date is None:
                start_date = datetime.utcnow() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.utcnow()
            
            # 遍历日期范围内的所有审计日志文件
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                audit_file = self.audit_dir / f"audit_{date_str}.jsonl"
                
                if audit_file.exists():
                    try:
                        with open(audit_file, 'r') as f:
                            for line in f:
                                if not line.strip():
                                    continue
                                try:
                                    entry = json.loads(line)
                                    entry_date = datetime.fromisoformat(entry["timestamp"])
                                    
                                    # 应用过滤条件
                                    if entry_date < start_date or entry_date > end_date:
                                        continue
                                    if platform and entry.get("platform") != platform:
                                        continue
                                    if action and entry.get("action") != action.value:
                                        continue
                                    
                                    logs.append(entry)
                                except json.JSONDecodeError:
                                    continue
                    except Exception as e:
                        logger.warning(f"读取审计日志文件失败 {audit_file}: {e}")
                
                current_date += timedelta(days=1)
            
            # 按时间倒序排序
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # 限制返回数量
            return logs[:limit]
            
        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            return []
    
    def get_audit_summary(self, days: int = 30) -> Dict[str, Any]:
        """获取审计日志摘要"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        logs = self.get_audit_logs(start_date=start_date, end_date=end_date, limit=10000)
        
        summary = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "total_actions": len(logs),
            "actions_by_type": {},
            "actions_by_platform": {},
            "success_rate": 0,
            "failed_actions": 0,
        }
        
        success_count = 0
        for log in logs:
            # 按操作类型统计
            action_type = log.get("action", "unknown")
            summary["actions_by_type"][action_type] = summary["actions_by_type"].get(action_type, 0) + 1
            
            # 按平台统计
            platform = log.get("platform", "unknown")
            summary["actions_by_platform"][platform] = summary["actions_by_platform"].get(platform, 0) + 1
            
            # 统计成功率
            if log.get("success", False):
                success_count += 1
            else:
                summary["failed_actions"] += 1
        
        if len(logs) > 0:
            summary["success_rate"] = success_count / len(logs)
        
        return summary
    
    def list_platforms(self) -> list[str]:
        """列出所有已配置的平台"""
        platforms = set()
        
        # 从文件系统
        for cred_file in self.config_dir.glob("*.json"):
            if cred_file.name != ".encryption_key":
                platforms.add(cred_file.stem)
        
        # 从环境变量
        for key in os.environ.keys():
            if "_" in key:
                parts = key.split("_")
                if len(parts) >= 2:
                    platforms.add(parts[0].lower())
        
        return sorted(list(platforms))


_credential_manager: Optional[APICredentialManager] = None


def get_credential_manager() -> APICredentialManager:
    """获取凭证管理器实例"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = APICredentialManager()
    return _credential_manager

