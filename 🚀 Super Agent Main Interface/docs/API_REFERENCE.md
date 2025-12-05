# API 参考文档

## 概述

AI Stack Super Enhanced 提供完整的RESTful API接口，支持多租户认证、合规审计、安全策略管理等功能。

## 基础信息

### 认证方式

所有API请求都需要在Header中包含认证信息：

```http
Authorization: Bearer <access_token>
X-Tenant-ID: <tenant_id>
```

### 基础URL

- 开发环境: `http://localhost:8000/api/v1`
- 生产环境: `https://api.aistack.com/api/v1`

### 响应格式

所有API响应都遵循统一格式：

```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456789"
}
```

错误响应格式：

```json
{
    "success": false,
    "error": {
        "code": "AUTH_ERROR",
        "message": "认证失败",
        "details": {}
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456789"
}
```

## 认证API

### 用户登录

**POST** `/auth/login`

请求体：
```json
{
    "username": "admin",
    "password": "password123",
    "tenant_id": "tenant_001"
}
```

响应：
```json
{
    "success": true,
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "refresh_token_123",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "roles": ["admin"]
        }
    },
    "message": "登录成功"
}
```

### 刷新令牌

**POST** `/auth/refresh`

请求体：
```json
{
    "refresh_token": "refresh_token_123"
}
```

### 用户登出

**POST** `/auth/logout`

### 获取用户信息

**GET** `/auth/profile`

## 租户管理API

### 获取租户列表

**GET** `/tenants`

查询参数：
- `page` (可选): 页码，默认1
- `size` (可选): 每页大小，默认20
- `status` (可选): 状态过滤

响应：
```json
{
    "success": true,
    "data": {
        "tenants": [
            {
                "id": "tenant_001",
                "name": "示例租户",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "user_count": 10
            }
        ],
        "total": 1,
        "page": 1,
        "size": 20
    }
}
```

### 创建租户

**POST** `/tenants`

请求体：
```json
{
    "name": "新租户",
    "description": "租户描述",
    "contact_email": "contact@example.com",
    "max_users": 100
}
```

### 更新租户

**PUT** `/tenants/{tenant_id}`

### 删除租户

**DELETE** `/tenants/{tenant_id}`

## 合规审计API

### 获取审计日志

**GET** `/audit/logs`

查询参数：
- `start_time` (可选): 开始时间
- `end_time` (可选): 结束时间
- `user_id` (可选): 用户ID过滤
- `action` (可选): 操作类型过滤
- `resource_type` (可选): 资源类型过滤

响应：
```json
{
    "success": true,
    "data": {
        "logs": [
            {
                "id": "log_001",
                "user_id": 1,
                "username": "admin",
                "action": "login",
                "resource_type": "auth",
                "resource_id": "user_1",
                "ip_address": "192.168.1.1",
                "timestamp": "2024-01-01T00:00:00Z",
                "details": {"success": true}
            }
        ],
        "total": 100,
        "page": 1,
        "size": 20
    }
}
```

### 创建审计记录

**POST** `/audit/logs`

请求体：
```json
{
    "action": "create_user",
    "resource_type": "user",
    "resource_id": "user_123",
    "details": {
        "username": "new_user",
        "roles": ["user"]
    }
}
```

## 安全策略API

### 获取安全策略

**GET** `/security/policies`

响应：
```json
{
    "success": true,
    "data": {
        "policies": [
            {
                "id": "policy_001",
                "name": "密码策略",
                "type": "password",
                "enabled": true,
                "config": {
                    "min_length": 8,
                    "require_uppercase": true,
                    "require_lowercase": true,
                    "require_numbers": true,
                    "require_special_chars": true
                }
            }
        ]
    }
}
```

### 更新安全策略

**PUT** `/security/policies/{policy_id}`

请求体：
```json
{
    "enabled": true,
    "config": {
        "min_length": 12,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_numbers": true,
        "require_special_chars": true
    }
}
```

### 执行安全检查

**POST** `/security/scan`

请求体：
```json
{
    "target": "user_input",
    "content": "需要检查的内容",
    "scan_type": "xss"
}
```

响应：
```json
{
    "success": true,
    "data": {
        "safe": true,
        "threats": [],
        "confidence": 0.95
    }
}
```

## 缓存管理API

### 获取缓存统计

**GET** `/cache/stats`

响应：
```json
{
    "success": true,
    "data": {
        "total_keys": 1000,
        "memory_used": "256MB",
        "hit_rate": 0.85,
        "miss_rate": 0.15,
        "evictions": 10
    }
}
```

### 清空缓存

**DELETE** `/cache/clear`

查询参数：
- `pattern` (可选): 缓存键模式

### 获取缓存键列表

**GET** `/cache/keys`

查询参数：
- `pattern` (可选): 键模式过滤
- `count` (可选): 返回数量，默认100

## 监控指标API

### 获取系统指标

**GET** `/monitoring/metrics`

响应：
```json
{
    "success": true,
    "data": {
        "cpu_usage": 45.2,
        "memory_usage": 65.8,
        "disk_usage": 30.1,
        "active_connections": 150,
        "request_rate": 120.5,
        "error_rate": 0.02
    }
}
```

### 获取应用指标

**GET** `/monitoring/app_metrics`

响应：
```json
{
    "success": true,
    "data": {
        "response_time": {
            "avg": 120,
            "p95": 250,
            "p99": 500
        },
        "throughput": 1000,
        "error_count": 5,
        "active_users": 50
    }
}
```

## 配置管理API

### 获取配置

**GET** `/config`

查询参数：
- `environment` (可选): 环境名称
- `namespace` (可选): 命名空间

响应：
```json
{
    "success": true,
    "data": {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "aistack"
        },
        "redis": {
            "host": "localhost",
            "port": 6379
        },
        "security": {
            "jwt_secret": "secret_key",
            "token_expire": 3600
        }
    }
}
```

### 更新配置

**PUT** `/config`

请求体：
```json
{
    "environment": "production",
    "config": {
        "database": {
            "host": "db.production.com"
        }
    }
}
```

## 错误码说明

### 认证相关错误

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| AUTH_INVALID_TOKEN | 无效的认证令牌 | 401 |
| AUTH_TOKEN_EXPIRED | 令牌已过期 | 401 |
| AUTH_PERMISSION_DENIED | 权限不足 | 403 |
| AUTH_TENANT_NOT_FOUND | 租户不存在 | 404 |

### 业务逻辑错误

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| VALIDATION_ERROR | 参数验证失败 | 400 |
| RESOURCE_NOT_FOUND | 资源不存在 | 404 |
| RESOURCE_CONFLICT | 资源冲突 | 409 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 | 429 |

### 系统错误

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| INTERNAL_ERROR | 内部服务器错误 | 500 |
| SERVICE_UNAVAILABLE | 服务不可用 | 503 |
| DATABASE_ERROR | 数据库错误 | 500 |

## 速率限制

API请求受到速率限制：

- 认证API: 10次/分钟
- 租户管理API: 100次/小时
- 审计API: 1000次/天
- 安全策略API: 50次/分钟

超过限制会返回429状态码和错误信息。

## SDK使用示例

### Python SDK

```python
from ai_stack_sdk import AIStackClient

# 初始化客户端
client = AIStackClient(
    base_url='http://localhost:8000/api/v1',
    access_token='your_access_token',
    tenant_id='your_tenant_id'
)

# 用户认证
result = client.auth.login('username', 'password')

# 获取租户信息
tenants = client.tenants.list()

# 创建审计记录
audit_log = client.audit.create_log(
    action='user_login',
    resource_type='auth',
    resource_id='user_123'
)
```

### JavaScript SDK

```javascript
import { AIStackClient } from 'ai-stack-sdk';

const client = new AIStackClient({
    baseUrl: 'http://localhost:8000/api/v1',
    accessToken: 'your_access_token',
    tenantId: 'your_tenant_id'
});

// 用户认证
const result = await client.auth.login('username', 'password');

// 获取监控指标
const metrics = await client.monitoring.getMetrics();
```

## 版本管理

API版本通过URL路径管理：

- v1: 当前稳定版本
- v2: 开发中版本（预览）

向后不兼容的变更会发布新版本，旧版本会继续维护一段时间。

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持多租户认证
- 实现合规审计功能
- 提供安全策略管理
- 集成分布式缓存

---

*文档版本: v1.0.0*  
*最后更新: 2024年1月*