# 采购管理模块运维手册

## 系统概述

采购管理模块是企业ERP系统的核心组件，负责采购全流程管理。本手册提供系统的运维指导。

## 系统架构

### 组件架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API网关层     │───▶│  业务逻辑层     │───▶│  数据访问层     │
│  procurement_api│    │procurement_manager│   │  数据库/缓存    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  监控告警层     │    │  配置管理层     │    │  健康检查层     │
│ project_monitor  │    │  config_manager  │   │  health_checker  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 部署环境

### 硬件要求
- **CPU**: 4核以上
- **内存**: 8GB以上
- **存储**: 100GB SSD
- **网络**: 1Gbps带宽

### 软件要求
- **操作系统**: Ubuntu 20.04+/CentOS 8+
- **Python**: 3.8+
- **数据库**: PostgreSQL 12+
- **缓存**: Redis 6+ (可选)
- **Web服务器**: Nginx 1.18+

## 安装部署

### 1. 环境准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础软件
sudo apt install -y python3 python3-pip postgresql postgresql-contrib redis-server nginx

# 创建专用用户
sudo useradd -r -s /bin/false procurement
sudo mkdir -p /opt/procurement
sudo chown procurement:procurement /opt/procurement
```

### 2. 数据库配置
```sql
-- 创建数据库和用户
CREATE DATABASE procurement_db;
CREATE USER procurement_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE procurement_db TO procurement_user;

-- 创建表结构（自动通过代码初始化）
```

### 3. 应用部署
```bash
# 切换到应用目录
cd /opt/procurement

# 克隆代码（或上传部署包）
git clone <repository-url> .

# 安装依赖
pip3 install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接等信息
```

### 4. 服务配置
```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/procurement.service > /dev/null <<EOF
[Unit]
Description=Procurement Management Service
After=network.target postgresql.service

[Service]
Type=simple
User=procurement
Group=procurement
WorkingDirectory=/opt/procurement
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 procurement_api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable procurement.service
sudo systemctl start procurement.service
```

### 5. Nginx配置
```nginx
# /etc/nginx/sites-available/procurement
server {
    listen 80;
    server_name procurement.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件缓存
    location /static/ {
        alias /opt/procurement/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 监控告警

### 监控指标

#### 1. 系统指标
- CPU使用率
- 内存使用率
- 磁盘I/O
- 网络带宽

#### 2. 应用指标
- API请求量
- 响应时间(P50/P95/P99)
- 错误率
- 数据库连接数
- 缓存命中率

#### 3. 业务指标
- 采购订单数量
- 订单处理时间
- 供应商绩效
- 库存周转率

### 告警规则

```yaml
# 告警规则配置
alert_rules:
  - name: "HighErrorRate"
    expr: "rate(http_requests_total{status=~'5..'}[5m]) > 0.05"
    for: "2m"
    labels:
      severity: "critical"
    annotations:
      summary: "高错误率告警"
      description: "5分钟内错误率超过5%"

  - name: "SlowResponse"
    expr: "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2"
    for: "5m"
    labels:
      severity: "warning"
    annotations:
      summary: "响应时间过长"
      description: "95%分位响应时间超过2秒"

  - name: "DatabaseDown"
    expr: "up{job='postgresql'} == 0"
    for: "1m"
    labels:
      severity: "critical"
    annotations:
      summary: "数据库不可用"
      description: "PostgreSQL服务异常"
```

## 备份恢复

### 数据备份策略

#### 1. 数据库备份
```bash
#!/bin/bash
# /opt/scripts/backup_procurement.sh

BACKUP_DIR="/backup/procurement"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR/$DATE

# 备份数据库
pg_dump -h localhost -U procurement_user procurement_db > $BACKUP_DIR/$DATE/procurement_db.sql

# 备份配置文件
cp -r /opt/procurement/config $BACKUP_DIR/$DATE/

# 压缩备份
tar -czf $BACKUP_DIR/procurement_backup_$DATE.tar.gz -C $BACKUP_DIR/$DATE .

# 清理临时文件
rm -rf $BACKUP_DIR/$DATE

# 保留最近7天备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

#### 2. 应用备份
```bash
# 备份应用代码和配置
tar -czf /backup/procurement_app_$(date +%Y%m%d).tar.gz /opt/procurement
```

### 恢复流程

#### 1. 数据库恢复
```bash
# 停止应用服务
sudo systemctl stop procurement.service

# 恢复数据库
psql -h localhost -U procurement_user -d procurement_db < /backup/procurement_db.sql

# 启动应用服务
sudo systemctl start procurement.service
```

#### 2. 应用恢复
```bash
# 解压备份文件
tar -xzf /backup/procurement_app_backup.tar.gz -C /opt/procurement

# 重新安装依赖
cd /opt/procurement && pip3 install -r requirements.txt

# 重启服务
sudo systemctl restart procurement.service
```

## 性能优化

### 数据库优化

#### 1. 索引优化
```sql
-- 采购订单表索引
CREATE INDEX idx_orders_status ON purchase_orders(status);
CREATE INDEX idx_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_orders_created ON purchase_orders(created_at);

-- 采购申请表索引
CREATE INDEX idx_requests_requester ON purchase_requests(requester);
CREATE INDEX idx_requests_status ON purchase_requests(status);

-- 供应商表索引
CREATE INDEX idx_suppliers_category ON suppliers(category);
CREATE INDEX idx_suppliers_performance ON suppliers(on_time_delivery_rate);
```

#### 2. 查询优化
- 使用EXPLAIN分析慢查询
- 避免SELECT *，只选择需要的字段
- 合理使用JOIN，避免N+1查询问题

### 应用优化

#### 1. 缓存策略
```python
# 缓存配置示例
CACHE_CONFIG = {
    'default_ttl': 300,  # 5分钟
    'max_size': 1000,    # 最大缓存条目
    'strategies': {
        'supplier_info': 3600,      # 供应商信息缓存1小时
        'order_list': 60,           # 订单列表缓存1分钟
        'performance_data': 1800,   # 绩效数据缓存30分钟
    }
}
```

#### 2. 连接池配置
```python
# 数据库连接池
DATABASE_POOL = {
    'min_connections': 5,
    'max_connections': 20,
    'timeout': 30
}
```

## 故障排除

### 常见问题

#### 1. 服务无法启动
**症状**: systemctl status procurement.service 显示失败
**排查步骤**:
1. 检查日志: `journalctl -u procurement.service -f`
2. 验证配置文件: `python3 -c "from config_manager import ConfigManager; print(ConfigManager().validate())"`
3. 检查端口占用: `netstat -tlnp | grep 8000`

#### 2. 数据库连接失败
**症状**: "Connection refused" 或 "Authentication failed"
**排查步骤**:
1. 检查PostgreSQL服务状态: `systemctl status postgresql`
2. 验证连接信息: `psql -h localhost -U procurement_user -d procurement_db`
3. 检查防火墙规则: `ufw status`

#### 3. 性能下降
**症状**: 响应时间变长，错误率升高
**排查步骤**:
1. 检查系统资源: `top`, `htop`, `iostat`
2. 分析慢查询: 启用PostgreSQL慢查询日志
3. 检查缓存命中率: Redis监控指标

### 日志分析

#### 日志文件位置
- 应用日志: `/var/log/procurement/procurement.log`
- 系统日志: `/var/log/syslog`
- Nginx日志: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`

#### 关键日志模式
```bash
# 搜索错误日志
grep -i "error\|exception\|failed" /var/log/procurement/procurement.log

# 搜索慢请求
grep "slow" /var/log/procurement/procurement.log

# 统计API调用
awk '{print $6 $7}' /var/log/nginx/access.log | sort | uniq -c | sort -nr
```

## 安全配置

### 1. 网络安全
```bash
# 配置防火墙
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 2. 应用安全
- 使用HTTPS加密传输
- 配置CORS策略
- 实现API认证和授权
- 定期更新依赖包

### 3. 数据安全
- 数据库连接使用SSL
- 敏感信息加密存储
- 定期安全扫描

## 版本升级

### 升级流程
1. 备份当前版本和数据
2. 停止服务
3. 更新代码
4. 运行数据库迁移
5. 启动服务
6. 验证功能

### 回滚流程
1. 停止服务
2. 恢复备份
3. 启动旧版本服务
4. 验证回滚成功

## 联系方式

### 运维团队
- **值班电话**: 400-xxx-xxxx
- **技术支持**: tech-support@example.com
- **紧急联系人**: 138-xxxx-xxxx

### 文档更新
本文档定期更新，最新版本请访问: https://docs.example.com/procurement/operations

---
*最后更新: 2025年11月12日*