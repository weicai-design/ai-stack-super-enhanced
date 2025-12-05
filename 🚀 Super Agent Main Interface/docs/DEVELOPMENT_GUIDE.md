# 开发指南

## 项目概述

AI Stack Super Enhanced 是一个高性能、可扩展的AI应用开发平台，提供多租户认证、合规审计、安全策略管理、分布式缓存等核心功能。

## 开发环境设置

### 前置要求

- Python 3.8+
- Docker & Docker Compose
- Git
- Redis (可选，用于缓存)
- PostgreSQL (可选，用于数据库)

### 环境配置

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-stack-super-enhanced
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **环境变量配置**
创建 `.env` 文件：
```bash
cp .env.example .env
# 编辑 .env 文件配置数据库、Redis等连接信息
```

## 项目结构

```
ai-stack-super-enhanced/
├── 🚀 Super Agent Main Interface/
│   ├── src/                    # 源代码目录
│   │   ├── auth/              # 认证模块
│   │   ├── audit/             # 审计模块
│   │   ├── cache/             # 缓存模块
│   │   ├── security/          # 安全模块
│   │   └── utils/             # 工具函数
│   ├── tests/                 # 测试代码
│   ├── docs/                  # 项目文档
│   ├── tools/                 # 开发工具
│   ├── deploy/                # 部署配置
│   └── config/                # 配置文件
├── docker-compose.yml         # Docker编排文件
├── Dockerfile                 # Docker镜像构建
├── requirements.txt           # Python依赖
└── README.md                  # 项目说明
```

## 开发规范

### 代码风格

项目遵循 PEP 8 代码风格规范：

```python
# 好的示例
def calculate_user_score(user_id: int, weight: float = 1.0) -> float:
    """计算用户评分
    
    Args:
        user_id: 用户ID
        weight: 权重系数，默认为1.0
        
    Returns:
        用户评分值
    """
    # 实现逻辑
    pass

# 避免的写法
def calc_score(uid,w=1.0):
    pass
```

### 类型注解

所有函数和方法都应使用类型注解：

```python
from typing import List, Dict, Optional

def process_users(users: List[Dict[str, Any]]) -> Optional[bool]:
    """处理用户列表"""
    pass
```

### 文档字符串

所有公共API都应包含完整的文档字符串：

```python
def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """用户认证
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        包含认证结果的字典:
        {
            'success': bool,
            'user_id': int,
            'token': str
        }
        
    Raises:
        AuthenticationError: 认证失败时抛出
    """
    pass
```

## 测试指南

### 测试结构

```
tests/
├── unit/              # 单元测试
├── integration/       # 集成测试
├── functional/        # 功能测试
└── fixtures/          # 测试数据
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_auth.py

# 生成测试覆盖率报告
pytest --cov=src tests/

# 并行运行测试
pytest -n auto
```

### 测试示例

```python
import pytest
from src.auth.tenant_auth import TenantAuthManager

class TestTenantAuthManager:
    """租户认证管理器测试"""
    
    @pytest.fixture
    def auth_manager(self):
        """创建认证管理器实例"""
        return TenantAuthManager()
    
    def test_authenticate_valid_user(self, auth_manager):
        """测试有效用户认证"""
        result = auth_manager.authenticate("admin", "password123")
        assert result["success"] is True
        assert "token" in result
    
    def test_authenticate_invalid_user(self, auth_manager):
        """测试无效用户认证"""
        result = auth_manager.authenticate("invalid", "wrongpass")
        assert result["success"] is False
        assert "error" in result
```

## 代码审查

### 审查流程

1. **创建Pull Request**
   - 描述变更内容
   - 关联相关Issue
   - 添加测试说明

2. **代码审查检查项**
   - [ ] 代码符合PEP 8规范
   - [ ] 包含适当的类型注解
   - [ ] 有完整的文档字符串
   - [ ] 包含单元测试
   - [ ] 测试通过且覆盖率达标
   - [ ] 没有安全漏洞
   - [ ] 性能优化考虑

3. **审查工具**
   - 使用 `black` 进行代码格式化
   - 使用 `mypy` 进行类型检查
   - 使用 `flake8` 进行代码质量检查
   - 使用 `bandit` 进行安全扫描

## 性能优化

### 缓存策略

```python
from src.cache.distributed_cache_manager import DistributedCacheManager

class UserService:
    def __init__(self):
        self.cache = DistributedCacheManager()
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户资料，使用缓存优化"""
        cache_key = f"user_profile:{user_id}"
        
        # 尝试从缓存获取
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # 缓存未命中，从数据库获取
        user_data = await self._fetch_from_db(user_id)
        
        # 设置缓存，过期时间1小时
        await self.cache.set(cache_key, user_data, expire=3600)
        
        return user_data
```

### 数据库优化

- 使用索引优化查询性能
- 避免N+1查询问题
- 使用连接池管理数据库连接
- 定期清理过期数据

## 安全开发

### 输入验证

```python
import re
from typing import Optional

def validate_email(email: str) -> Optional[str]:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    return None

def sanitize_input(input_str: str) -> str:
    """清理用户输入"""
    # 移除潜在的恶意字符
    cleaned = re.sub(r'[<>\"\']', '', input_str)
    return cleaned.strip()
```

### 密码安全

```python
import bcrypt

def hash_password(password: str) -> str:
    """哈希密码"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

## 部署与运维

### 本地开发部署

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 生产环境部署

```bash
# 构建生产镜像
docker build -t ai-stack:latest .

# 使用部署脚本部署
./deploy.sh production
```

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接参数
   - 检查网络连通性

2. **缓存服务异常**
   - 检查Redis服务状态
   - 验证缓存配置
   - 清理缓存数据

3. **性能问题**
   - 使用监控工具分析性能瓶颈
   - 检查数据库查询性能
   - 优化缓存策略

### 日志分析

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 记录结构化日志
logger.info("用户登录成功", extra={
    'user_id': user_id,
    'ip_address': ip_address,
    'action': 'login'
})
```

## 贡献指南

### 提交代码

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 提交信息规范

```
类型(范围): 简要描述

详细描述

BREAKING CHANGE: 破坏性变更说明（如有）
```

类型包括：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建过程或辅助工具变动

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 讨论区: [Discussions]
- 文档网站: [Documentation]

---

*最后更新: 2024年1月*