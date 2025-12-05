"""
API Key 数据库存储模块
API Key Database Storage Module

使用 SQLite 存储 API Key 信息，实现持久化存储

版本: v3.1.0
"""

from __future__ import annotations

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

from .auth import APIKey, APIKeyScope

logger = logging.getLogger(__name__)


class APIKeyDatabase:
    """API Key 数据库管理"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径（如果为None，使用默认路径）
        """
        if db_path is None:
            # 默认路径：项目根目录下的 data 文件夹
            project_root = Path(__file__).parent.parent.parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "api_keys.db")
        
        self.db_path = db_path
        self.conn = None
        self._init_database()
        logger.info(f"✅ API Key 数据库已初始化: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # 设置行工厂，返回字典格式
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def _init_database(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建 API Keys 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                scopes TEXT NOT NULL,
                allowed_commands TEXT,
                rate_limit INTEGER,
                expires_at TEXT,
                last_used_at TEXT,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                metadata TEXT
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_id ON api_keys(tenant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON api_keys(is_active)")
        
        # 创建 Token 黑名单表（用于 Token 撤销）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_blacklist (
                token_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                user_id TEXT,
                expires_at TEXT NOT NULL,
                revoked_at TEXT NOT NULL,
                reason TEXT
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_blacklist_tenant ON token_blacklist(tenant_id)")
        
        # 创建审计日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_logs(tenant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)")
        
        conn.commit()
        logger.info("✅ 数据库表已创建")
    
    def save_api_key(self, api_key: APIKey) -> bool:
        """保存 API Key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO api_keys 
                (id, tenant_id, name, key_hash, scopes, allowed_commands, rate_limit, 
                 expires_at, last_used_at, created_at, is_active, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                api_key.id,
                api_key.tenant_id,
                api_key.name,
                api_key.key_hash,
                json.dumps([scope.value for scope in api_key.scopes]),
                json.dumps(api_key.allowed_commands) if api_key.allowed_commands else None,
                api_key.rate_limit,
                api_key.expires_at.isoformat() if api_key.expires_at else None,
                api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                api_key.created_at.isoformat(),
                1 if api_key.is_active else 0,
                json.dumps(api_key.metadata)
            ))
            
            conn.commit()
            logger.debug(f"✅ API Key 已保存: {api_key.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存 API Key 失败: {e}")
            conn.rollback()
            return False
    
    def get_api_key_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """通过 key_hash 获取 API Key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM api_keys WHERE key_hash = ?", (key_hash,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_api_key(row)
    
    def get_api_key_by_id(self, key_id: str) -> Optional[APIKey]:
        """通过 ID 获取 API Key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_api_key(row)
    
    def list_tenant_api_keys(self, tenant_id: str) -> List[APIKey]:
        """列出租户的 API Keys"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM api_keys WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,))
        rows = cursor.fetchall()
        
        return [self._row_to_api_key(row) for row in rows]
    
    def update_api_key(self, api_key: APIKey) -> bool:
        """更新 API Key"""
        return self.save_api_key(api_key)
    
    def revoke_api_key(self, key_id: str) -> bool:
        """撤销 API Key（标记为非激活）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
            conn.commit()
            logger.info(f"✅ API Key 已撤销: {key_id}")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ 撤销 API Key 失败: {e}")
            conn.rollback()
            return False
    
    def update_last_used(self, key_id: str, last_used_at: datetime):
        """更新最后使用时间"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (last_used_at.isoformat(), key_id)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"❌ 更新最后使用时间失败: {e}")
    
    def _row_to_api_key(self, row) -> APIKey:
        """将数据库行转换为 APIKey 对象"""
        scopes = [APIKeyScope(scope) for scope in json.loads(row["scopes"])]
        allowed_commands = json.loads(row["allowed_commands"]) if row["allowed_commands"] else []
        
        expires_at = None
        if row["expires_at"]:
            expires_at = datetime.fromisoformat(row["expires_at"])
        
        last_used_at = None
        if row["last_used_at"]:
            last_used_at = datetime.fromisoformat(row["last_used_at"])
        
        created_at = datetime.fromisoformat(row["created_at"])
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        
        return APIKey(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            key_hash=row["key_hash"],
            scopes=scopes,
            allowed_commands=allowed_commands,
            rate_limit=row["rate_limit"],
            expires_at=expires_at,
            last_used_at=last_used_at,
            created_at=created_at,
            is_active=bool(row["is_active"]),
            metadata=metadata
        )
    
    # ==================== Token 黑名单管理 ====================
    
    def add_token_to_blacklist(self, token_id: str, tenant_id: str, user_id: Optional[str], 
                               expires_at: datetime, reason: Optional[str] = None):
        """添加 Token 到黑名单"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO token_blacklist 
                (token_id, tenant_id, user_id, expires_at, revoked_at, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                token_id,
                tenant_id,
                user_id,
                expires_at.isoformat(),
                datetime.now().isoformat(),
                reason
            ))
            
            conn.commit()
            logger.info(f"✅ Token 已加入黑名单: {token_id}")
            
        except Exception as e:
            logger.error(f"❌ 添加 Token 到黑名单失败: {e}")
            conn.rollback()
    
    def is_token_blacklisted(self, token_id: str) -> bool:
        """检查 Token 是否在黑名单中"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 1 FROM token_blacklist 
            WHERE token_id = ? AND expires_at > ?
        """, (token_id, datetime.now().isoformat()))
        
        return cursor.fetchone() is not None
    
    def cleanup_expired_tokens(self):
        """清理过期的 Token（黑名单）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM token_blacklist WHERE expires_at < ?", (datetime.now().isoformat(),))
            conn.commit()
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(f"✅ 已清理 {deleted} 个过期的 Token")
        except Exception as e:
            logger.error(f"❌ 清理过期 Token 失败: {e}")
    
    # ==================== 审计日志 ====================
    
    def add_audit_log(self, tenant_id: str, action: str, resource_type: str,
                     resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                     user_id: Optional[str] = None, ip_address: Optional[str] = None,
                     user_agent: Optional[str] = None):
        """添加审计日志"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO audit_logs 
                (tenant_id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tenant_id,
                user_id,
                action,
                resource_type,
                resource_id,
                json.dumps(details) if details else None,
                ip_address,
                user_agent,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.debug(f"✅ 审计日志已添加: {action}")
            
        except Exception as e:
            logger.error(f"❌ 添加审计日志失败: {e}")
            conn.rollback()
    
    def get_audit_logs(self, tenant_id: Optional[str] = None, action: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            {
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "user_id": row["user_id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "details": json.loads(row["details"]) if row["details"] else None,
                "ip_address": row["ip_address"],
                "user_agent": row["user_agent"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# ==================== 全局实例 ====================

# 创建全局数据库实例
_db_instance: Optional[APIKeyDatabase] = None


def get_database() -> APIKeyDatabase:
    """获取数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = APIKeyDatabase()
    return _db_instance


# ==================== 导出 ====================

__all__ = ["APIKeyDatabase", "get_database"]




