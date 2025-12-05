#!/usr/bin/env python3
"""
采购管理模块数据库迁移脚本
支持版本升级和回滚
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """数据库迁移管理器"""
    
    def __init__(self, database_url):
        """初始化迁移器"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.migrations_table = "schema_migrations"
        
    def ensure_migrations_table(self):
        """确保迁移表存在"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.migrations_table} (
            version VARCHAR(50) PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_by VARCHAR(100)
        )
        """
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(create_table_sql))
                conn.commit()
            logger.info("迁移表已创建或已存在")
        except SQLAlchemyError as e:
            logger.error(f"创建迁移表失败: {e}")
            raise
    
    def get_applied_migrations(self):
        """获取已应用的迁移"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT version FROM {self.migrations_table} ORDER BY applied_at")
                )
                return [row[0] for row in result]
        except SQLAlchemyError as e:
            logger.error(f"获取已应用迁移失败: {e}")
            return []
    
    def apply_migration(self, version, description, sql_script):
        """应用单个迁移"""
        try:
            with self.engine.connect() as conn:
                # 执行迁移SQL
                conn.execute(text(sql_script))
                
                # 记录迁移历史
                insert_sql = f"""
                INSERT INTO {self.migrations_table} (version, description, applied_by)
                VALUES (:version, :description, :applied_by)
                """
                conn.execute(
                    text(insert_sql),
                    {
                        "version": version,
                        "description": description,
                        "applied_by": "migration_script"
                    }
                )
                conn.commit()
                
            logger.info(f"迁移 {version} 应用成功: {description}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"应用迁移 {version} 失败: {e}")
            return False
    
    def rollback_migration(self, version):
        """回滚单个迁移"""
        # 这里需要根据具体迁移实现回滚逻辑
        # 实际项目中应该有对应的回滚SQL
        logger.warning(f"回滚迁移 {version} - 需要手动实现回滚逻辑")
        return False
    
    def migrate_to_latest(self):
        """迁移到最新版本"""
        logger.info("开始数据库迁移...")
        
        # 确保迁移表存在
        self.ensure_migrations_table()
        
        # 获取已应用的迁移
        applied_migrations = self.get_applied_migrations()
        logger.info(f"已应用迁移: {applied_migrations}")
        
        # 定义所有迁移（按版本顺序）
        migrations = [
            # 版本 1.0.0 - 初始版本
            {
                "version": "1.0.0",
                "description": "初始表结构创建",
                "sql": """
                -- 创建采购申请表
                CREATE TABLE IF NOT EXISTS purchase_requests (
                    request_id SERIAL PRIMARY KEY,
                    requester VARCHAR(100) NOT NULL,
                    items JSONB NOT NULL,
                    total_amount DECIMAL(15,2),
                    reason TEXT,
                    required_date DATE,
                    priority VARCHAR(20) DEFAULT 'medium',
                    status VARCHAR(20) DEFAULT 'pending',
                    approved_by VARCHAR(100),
                    approval_notes TEXT,
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 创建采购订单表
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    order_id SERIAL PRIMARY KEY,
                    request_id INTEGER REFERENCES purchase_requests(request_id),
                    supplier_id INTEGER NOT NULL,
                    order_number VARCHAR(50) UNIQUE,
                    items JSONB NOT NULL,
                    total_amount DECIMAL(15,2),
                    status VARCHAR(20) DEFAULT 'draft',
                    expected_delivery_date DATE,
                    actual_delivery_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 创建供应商表
                CREATE TABLE IF NOT EXISTS suppliers (
                    supplier_id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    category VARCHAR(100),
                    contact_person VARCHAR(100),
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    address TEXT,
                    rating DECIMAL(3,2) DEFAULT 0.0,
                    on_time_delivery_rate DECIMAL(5,2) DEFAULT 0.0,
                    quality_rating DECIMAL(5,2) DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 创建收货记录表
                CREATE TABLE IF NOT EXISTS goods_receipts (
                    receipt_id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES purchase_orders(order_id),
                    received_quantity INTEGER,
                    quality_status VARCHAR(50),
                    received_by VARCHAR(100),
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                );
                
                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_requests_status ON purchase_requests(status);
                CREATE INDEX IF NOT EXISTS idx_requests_requester ON purchase_requests(requester);
                CREATE INDEX IF NOT EXISTS idx_orders_status ON purchase_orders(status);
                CREATE INDEX IF NOT EXISTS idx_orders_supplier ON purchase_orders(supplier_id);
                CREATE INDEX IF NOT EXISTS idx_suppliers_category ON suppliers(category);
                CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(is_active);
                """
            },
            
            # 版本 1.1.0 - 添加审计字段和性能优化
            {
                "version": "1.1.0",
                "description": "添加审计字段和性能优化",
                "sql": """
                -- 添加审计字段到采购订单表
                ALTER TABLE purchase_orders 
                ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
                ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100);
                
                -- 添加审计字段到采购申请表
                ALTER TABLE purchase_requests 
                ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
                ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100);
                
                -- 创建采购统计表
                CREATE TABLE IF NOT EXISTS procurement_stats (
                    stat_id SERIAL PRIMARY KEY,
                    stat_date DATE NOT NULL,
                    total_orders INTEGER DEFAULT 0,
                    total_amount DECIMAL(15,2) DEFAULT 0.0,
                    avg_processing_time INTERVAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 添加唯一索引
                CREATE UNIQUE INDEX IF NOT EXISTS idx_stats_date ON procurement_stats(stat_date);
                
                -- 优化查询性能
                CREATE INDEX IF NOT EXISTS idx_orders_created ON purchase_orders(created_at);
                CREATE INDEX IF NOT EXISTS idx_requests_created ON purchase_requests(created_at);
                """
            },
            
            # 版本 1.2.0 - 添加配置表和监控功能
            {
                "version": "1.2.0",
                "description": "添加配置表和监控功能",
                "sql": """
                -- 创建配置表
                CREATE TABLE IF NOT EXISTS system_config (
                    config_id SERIAL PRIMARY KEY,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value TEXT,
                    config_type VARCHAR(50) DEFAULT 'string',
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 创建监控指标表
                CREATE TABLE IF NOT EXISTS monitoring_metrics (
                    metric_id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(15,4),
                    metric_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags JSONB
                );
                
                -- 插入默认配置
                INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
                ('rate_limit_capacity', '100', 'integer', 'API限流容量'),
                ('rate_limit_rate', '10', 'integer', 'API限流速率'),
                ('circuit_breaker_threshold', '5', 'integer', '熔断器失败阈值'),
                ('cache_ttl', '300', 'integer', '缓存生存时间（秒）'),
                ('default_page_size', '20', 'integer', '默认分页大小')
                ON CONFLICT (config_key) DO NOTHING;
                
                -- 创建监控索引
                CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON monitoring_metrics(metric_name, metric_timestamp);
                """
            }
        ]
        
        # 应用未应用的迁移
        applied_count = 0
        for migration in migrations:
            if migration["version"] not in applied_migrations:
                logger.info(f"应用迁移: {migration['version']} - {migration['description']}")
                
                if self.apply_migration(
                    migration["version"], 
                    migration["description"], 
                    migration["sql"]
                ):
                    applied_count += 1
                else:
                    logger.error(f"迁移失败，停止后续迁移")
                    break
        
        if applied_count > 0:
            logger.info(f"成功应用 {applied_count} 个迁移")
        else:
            logger.info("数据库已是最新版本，无需迁移")
        
        return applied_count

def main():
    """主函数"""
    # 从环境变量获取数据库连接信息
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("请设置 DATABASE_URL 环境变量")
        sys.exit(1)
    
    # 创建迁移器并执行迁移
    migrator = DatabaseMigrator(database_url)
    
    try:
        applied_count = migrator.migrate_to_latest()
        
        if applied_count > 0:
            logger.info("数据库迁移完成")
        else:
            logger.info("数据库已是最新版本")
            
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()