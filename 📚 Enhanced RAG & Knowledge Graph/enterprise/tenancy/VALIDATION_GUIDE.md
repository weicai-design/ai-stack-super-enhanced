# 多租户认证系统验证指南

## 概述

本指南提供了完整的多租户认证和授权系统验证步骤，确保系统在生产环境部署前正常运行。

## 快速验证（推荐）

运行综合验证脚本，会自动完成所有检查：

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/validate_system.py"
```

此脚本会：
1. 运行系统完整性检查
2. 运行集成测试
3. 生成验证报告（`validation_report.txt`）

## 详细验证步骤

### 步骤 1: 安装依赖

如果依赖包未安装，运行安装脚本：

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
bash "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/install_dependencies.sh"
```

或手动安装：

```bash
pip install pydantic fastapi python-jose[cryptography] passlib[bcrypt] python-dotenv
```

### 步骤 2: 系统完整性检查

检查系统环境、依赖、配置等：

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/check_system_integrity.py"
```

**检查项：**
- ✅ Python 版本（推荐 3.11+）
- ✅ 依赖包（pydantic, fastapi, python-jose, passlib, sqlite3）
- ✅ 环境变量配置（JWT_SECRET_KEY 等）
- ✅ 数据库连接（SQLite）
- ✅ 模块导入（enterprise.tenancy.*）
- ✅ 文件系统权限（logs, data 目录）

### 步骤 3: 集成测试

运行完整的集成测试：

```bash
cd "/Users/ywc/ai-stack-super-enhanced"
python3 "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/test_integration.py"
```

**测试项：**
- ✅ 模块导入
- ✅ JWT Token 生成、验证、撤销
- ✅ API Key 生成、验证、权限控制、撤销
- ✅ 命令白名单分类
- ✅ tenant_context 绑定
- ✅ 数据库存储（API Keys、Token 黑名单、审计日志）
- ✅ 审计日志记录和查询

## 验证结果说明

### ✅ 通过
- 所有功能正常工作
- 系统可以正常使用
- 可以部署到生产环境

### ⚠️ 警告
- 部分功能可能无法正常工作
- 建议检查警告信息
- 某些可选功能可能不可用
- 可以继续使用，但建议修复警告

### ❌ 失败
- 系统存在问题，需要修复
- 检查错误信息
- 参考"常见问题"部分
- 不要部署到生产环境，直到所有检查通过

## 常见问题

### 1. ModuleNotFoundError: No module named 'pydantic'

**问题**: 缺少 Python 依赖包

**解决方案**: 
```bash
# 运行安装脚本
bash "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/install_dependencies.sh"

# 或手动安装
pip install pydantic fastapi python-jose[cryptography] passlib[bcrypt] python-dotenv
```

### 2. ModuleNotFoundError: No module named 'enterprise'

**问题**: Python 路径配置不正确

**解决方案**: 
- 确保在项目根目录运行脚本
- 检查脚本路径是否正确
- 确保 "📚 Enhanced RAG & Knowledge Graph" 目录存在

### 3. JWT Secret Key 未配置

**问题**: `.env` 文件中缺少 `JWT_SECRET_KEY`

**解决方案**:
```bash
# 1. 复制环境变量示例文件
cp env.example .env

# 2. 生成 JWT Secret Key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 编辑 .env 文件，设置 JWT_SECRET_KEY
# JWT_SECRET_KEY=your-generated-secret-key-here
```

### 4. SQLite 数据库错误

**问题**: SQLite 数据库连接失败

**解决方案**:
```bash
# 1. 检查 SQLite 是否可用
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"

# 2. 检查数据库目录权限
ls -ld data/
chmod 755 data/

# 3. 检查磁盘空间
df -h
```

### 5. 数据库表不存在

**问题**: SQLite 数据库表未初始化

**解决方案**: 
- 首次运行会自动创建表
- 如果表不存在，删除数据库文件重新运行：
```bash
rm -f data/tenancy.db
# 重新运行测试脚本，会自动创建表
```

## 验证报告

运行 `validate_system.py` 后，会在项目根目录生成 `validation_report.txt` 文件，包含：

- ✅ 验证时间戳
- ✅ 完整性检查结果
- ✅ 集成测试结果
- ✅ 详细错误信息（如有）
- ✅ 建议的修复步骤

查看报告：
```bash
cat validation_report.txt
```

## 下一步

验证通过后，可以：

1. **启动 API Gateway 服务**
   ```bash
   python3 api-gateway/gateway.py
   ```

2. **使用权限管理页面**
   - 打开 `📚 Enhanced RAG & Knowledge Graph/web/permission_management.html`
   - 创建和管理 API Keys
   - 设置命令权限

3. **在 API 请求中使用认证**
   - 使用 JWT Token: `Authorization: Bearer <token>`
   - 使用 API Key: `X-API-Key: <api-key>`

4. **查看审计日志**
   - 通过 API: `GET /api/tenant/auth/audit-logs`
   - 查看数据库: `sqlite3 data/tenancy.db "SELECT * FROM audit_logs;"`

## 验证清单

在部署到生产环境前，确保：

- [ ] 所有完整性检查通过
- [ ] 所有集成测试通过
- [ ] JWT_SECRET_KEY 已设置且足够强（至少32字符）
- [ ] API_KEY_SALT 已设置
- [ ] 数据库文件有备份
- [ ] 日志目录有写入权限
- [ ] 环境变量已正确配置
- [ ] 验证报告已生成并审查
- [ ] 所有依赖包已安装
- [ ] Python 版本符合要求（3.11+）

## 支持

如有问题，请：
1. 查看验证报告中的错误信息
2. 检查 `TEST_README.md` 文档
3. 查看系统日志：`logs/security_audit.log`
4. 检查数据库：`sqlite3 data/tenancy.db`














