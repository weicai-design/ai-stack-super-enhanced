# 多租户认证系统测试说明

## 验证脚本

系统提供了完整的验证和测试脚本：

### 1. 系统完整性检查脚本

**`check_system_integrity.py`** - 系统完整性检查（推荐首先运行）
- Python 版本检查
- 依赖包检查和安装提示
- 环境变量配置检查
- 数据库连接检查
- 模块导入检查
- 文件系统权限检查

**运行方式：**
```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/check_system_integrity.py"
```

### 2. 依赖安装脚本

**`install_dependencies.sh`** - 自动安装依赖包
- 安装核心依赖包（pydantic, fastapi, python-jose, passlib, python-dotenv）
- 安装可选依赖包（cryptography, PyJWT）

**运行方式：**
```bash
cd "/Users/ywc/ai-stack-super-enhanced"
bash "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/install_dependencies.sh"
```

### 3. 综合验证脚本

**`validate_system.py`** - 综合验证（推荐用于完整验证）
- 运行系统完整性检查
- 运行集成测试
- 生成验证报告

**运行方式：**
```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/validate_system.py"
```

### 4. 集成测试脚本

**`test_integration.py`** - 集成测试（全面验证）
- 模块导入
- JWT Token 生成、验证、撤销
- API Key 生成、验证、权限控制、撤销
- 命令白名单分类
- tenant_context 绑定
- 数据库存储（SQLite）
- 审计日志

**运行方式：**
```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/test_integration.py"
```

### 5. 基础功能测试脚本（可选）

**`test_auth.py`** - 基础功能测试（快速验证）
- 模块导入
- JWT Token 生成和验证
- API Key 生成和验证
- 命令白名单分类

## 快速开始

### 方式 1: 自动验证（推荐）

运行综合验证脚本，会自动进行完整性检查和集成测试：

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/validate_system.py"
```

### 方式 2: 手动步骤

#### 步骤 1: 安装依赖

如果依赖包未安装，运行安装脚本：

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
bash "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/install_dependencies.sh"
```

或手动安装：

```bash
pip install pydantic fastapi python-jose[cryptography] passlib[bcrypt] python-dotenv
```

#### 步骤 2: 运行完整性检查

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/check_system_integrity.py"
```

#### 步骤 3: 运行集成测试

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/test_integration.py"
```

## 运行要求

### 1. 依赖包安装

测试脚本需要以下 Python 包：

```bash
pip install pydantic fastapi python-jose[cryptography] passlib[bcrypt] python-dotenv
```

### 2. 环境变量配置

确保 `.env` 文件已配置：

```bash
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
API_KEY_USE_DATABASE=true
TOKEN_REVOCATION_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

## 验证结果说明

### ✅ 通过
- 所有功能正常工作
- 可以继续使用系统
- 可以部署到生产环境

### ⚠️ 警告
- 部分功能可能无法正常工作
- 建议检查警告信息
- 某些可选功能可能不可用

### ❌ 失败
- 检查错误信息
- 确认依赖包是否安装
- 确认环境变量是否配置
- 确认 SQLite 数据库是否可用
- 运行 `install_dependencies.sh` 安装缺失的依赖

## 验证报告

运行 `validate_system.py` 后，会在项目根目录生成 `validation_report.txt` 文件，包含：
- 完整性检查结果
- 集成测试结果
- 详细错误信息（如有）
- 建议的修复步骤

## 常见问题

### 1. ModuleNotFoundError: No module named 'pydantic'
**解决方案**: 安装依赖包
```bash
pip install pydantic fastapi python-jose[cryptography] passlib[bcrypt] sqlalchemy
```

### 2. ModuleNotFoundError: No module named 'enterprise'
**解决方案**: 确保在项目根目录运行，或检查路径是否正确

### 3. SQLite 数据库错误
**解决方案**: 
- 确认 SQLite3 已安装：`python3 -c "import sqlite3; print(sqlite3.sqlite_version)"`
- 确认数据库目录有写入权限

### 4. JWT Secret Key 未配置
**解决方案**: 在 `.env` 文件中设置 `JWT_SECRET_KEY`

## 测试覆盖范围

### ✅ 已测试功能
- JWT Token 生成和验证
- JWT Token 撤销（黑名单）
- API Key 生成和验证
- API Key 撤销
- API Key 权限控制（命令白名单）
- 租户上下文绑定
- 数据库存储（API Keys、Token 黑名单、审计日志）
- 审计日志记录和查询

### 📝 待测试功能（可选）
- API Gateway 集成
- 多租户数据隔离
- 速率限制
- 并发访问

## 下一步

测试通过后，可以：
1. 启动 API Gateway 服务
2. 使用权限管理页面创建 API Keys
3. 在 API 请求中使用 JWT Token 或 API Key
4. 查看审计日志

