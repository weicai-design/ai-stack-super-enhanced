# 🔧 API密钥配置向导

## 概述

API配置向导帮助您快速配置AI-Stack系统所需的所有外部API密钥，包括股票交易、内容发布等第三方服务。

## 功能特性

### 支持的API服务

| 服务名称 | 优先级 | 用途 | 功能模块 |
|---------|--------|------|---------|
| 同花顺 | 🔴 高 | 股票交易 | 实时行情、历史数据、股票交易 |
| 小红书 | 🟡 中 | 内容发布 | 内容发布、数据统计、粉丝管理 |
| 抖音 | 🟡 中 | 短视频发布 | 视频发布、数据分析、互动管理 |
| 知乎 | 🟢 低 | 文章发布 | 文章发布、数据统计 |
| 今日头条 | 🟢 低 | 内容分发 | 文章发布、视频发布、数据分析 |

## 快速开始

### 1. 查看配置指南

```bash
cd "🔧 API配置向导"
python api_key_configurator.py --guide
```

### 2. 创建.env配置文件

```bash
# 创建配置文件模板
python api_key_configurator.py --create-env

# 强制覆盖现有文件
python api_key_configurator.py --create-env --force
```

### 3. 编辑配置文件

打开项目根目录下的 `.env` 文件，填入您申请的API密钥：

```bash
# 编辑配置文件
nano ../env

# 或使用其他编辑器
code ../.env
```

### 4. 验证配置

```bash
# 验证所有API配置
python api_key_configurator.py --validate
```

## 详细使用

### Python代码方式配置

```python
from api_key_configurator import APIKeyConfigurator

# 创建配置器实例
configurator = APIKeyConfigurator()

# 方式1: 设置单个服务的API密钥
result = configurator.set_api_key(
    service_name="同花顺",
    key_value_pairs={
        "THS_API_KEY": "your_actual_api_key",
        "THS_SECRET_KEY": "your_actual_secret_key"
    }
)
print(result)

# 方式2: 验证配置
validation_result = configurator.validate_configuration()
print(validation_result["summary"])

# 方式3: 验证特定服务
validation_result = configurator.validate_configuration(service_name="同花顺")
print(validation_result["summary"])
```

### 批量配置示例

```python
from api_key_configurator import APIKeyConfigurator

configurator = APIKeyConfigurator()

# 配置所有API密钥
api_configs = {
    "同花顺": {
        "THS_API_KEY": "your_ths_key",
        "THS_SECRET_KEY": "your_ths_secret"
    },
    "小红书": {
        "XHS_API_KEY": "your_xhs_key",
        "XHS_APP_ID": "your_app_id",
        "XHS_APP_SECRET": "your_app_secret"
    }
}

for service, keys in api_configs.items():
    result = configurator.set_api_key(service, keys)
    print(f"{service}: {result['message']}")
```

## API密钥申请指南

### 同花顺API（股票交易）

1. **注册地址**: https://open.10jqka.com.cn/
2. **申请步骤**:
   - 注册开发者账号
   - 实名认证
   - 创建应用
   - 获取API Key和Secret Key
3. **所需密钥**:
   - `THS_API_KEY`: API密钥
   - `THS_SECRET_KEY`: 密钥密码

### 小红书API（内容发布）

1. **注册地址**: https://open.xiaohongshu.com/
2. **申请步骤**:
   - 注册企业账号
   - 提交资质审核
   - 创建应用
   - 获取App ID和App Secret
3. **所需密钥**:
   - `XHS_API_KEY`: API密钥
   - `XHS_APP_ID`: 应用ID
   - `XHS_APP_SECRET`: 应用密钥

### 抖音API（短视频）

1. **注册地址**: https://open.douyin.com/
2. **申请步骤**:
   - 注册开放平台账号
   - 创建应用
   - 获取Client Key和Client Secret
3. **所需密钥**:
   - `DOUYIN_API_KEY`: API密钥
   - `DOUYIN_APP_ID`: 客户端ID
   - `DOUYIN_APP_SECRET`: 客户端密钥

### 知乎API（内容发布）

1. **注册地址**: https://open.zhihu.com/
2. **申请步骤**:
   - 登录知乎账号
   - 进入开放平台
   - 创建应用
3. **所需密钥**:
   - `ZHIHU_API_KEY`: API密钥
   - `ZHIHU_APP_ID`: 应用ID

### 今日头条API（内容分发）

1. **注册地址**: https://open.toutiao.com/
2. **申请步骤**:
   - 注册头条号
   - 申请开放平台权限
   - 创建应用
3. **所需密钥**:
   - `TOUTIAO_API_KEY`: API密钥
   - `TOUTIAO_APP_ID`: 应用ID
   - `TOUTIAO_APP_SECRET`: 应用密钥

## 配置文件说明

### .env文件结构

```bash
# AI-Stack API配置文件

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 核心服务配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:14b
DATABASE_URL=sqlite:///./ai_stack.db

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 股票交易API（高优先级）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THS_API_KEY=your_ths_api_key_here
THS_SECRET_KEY=your_ths_secret_key_here

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 内容发布API（中优先级）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

XHS_API_KEY=your_xhs_api_key_here
XHS_APP_ID=your_app_id_here
XHS_APP_SECRET=your_app_secret_here

DOUYIN_API_KEY=your_douyin_api_key_here
DOUYIN_APP_ID=your_app_id_here
DOUYIN_APP_SECRET=your_app_secret_here

# ... 其他配置
```

## 安全最佳实践

### 1. 密钥保护

- ✅ **DO**: 将 `.env` 添加到 `.gitignore`
- ✅ **DO**: 定期更换API密钥
- ✅ **DO**: 使用环境变量存储密钥
- ❌ **DON'T**: 将密钥硬编码在代码中
- ❌ **DON'T**: 将 `.env` 文件提交到Git仓库
- ❌ **DON'T**: 在公开场合分享密钥

### 2. 权限控制

```bash
# 设置.env文件权限（仅所有者可读写）
chmod 600 .env
```

### 3. 密钥轮换

建议每3-6个月更换一次API密钥，特别是高优先级的密钥。

## 故障排查

### 问题1: 配置文件不生效

**解决方案**:
```bash
# 检查.env文件是否存在
ls -la ../.env

# 验证配置
python api_key_configurator.py --validate

# 重启相关服务
cd ..
./scripts/restart_services.sh
```

### 问题2: API密钥无效

**解决方案**:
1. 确认密钥是否正确复制（无多余空格）
2. 检查密钥是否已过期
3. 验证API服务是否正常
4. 查看服务日志获取详细错误信息

### 问题3: 部分服务配置缺失

这是正常的！您只需配置要使用的服务即可。未配置的服务不会影响其他功能。

## 命令行参数

```bash
# 显示配置指南
python api_key_configurator.py --guide

# 验证API配置
python api_key_configurator.py --validate

# 创建.env模板文件
python api_key_configurator.py --create-env

# 强制覆盖现有.env文件
python api_key_configurator.py --create-env --force
```

## 集成到其他服务

### 在FastAPI中使用

```python
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 使用API密钥
ths_api_key = os.getenv("THS_API_KEY")
ths_secret_key = os.getenv("THS_SECRET_KEY")

if ths_api_key and ths_secret_key:
    # 初始化股票交易客户端
    pass
```

### 在Docker中使用

```yaml
# docker-compose.yml
services:
  ai-stack:
    env_file:
      - .env
    environment:
      - THS_API_KEY=${THS_API_KEY}
      - THS_SECRET_KEY=${THS_SECRET_KEY}
```

## 常见问题

### Q: 必须配置所有API吗？

A: 不是。只配置您需要使用的功能对应的API即可。例如，如果您不使用股票交易功能，可以跳过同花顺API的配置。

### Q: 如何知道密钥是否配置正确？

A: 运行 `python api_key_configurator.py --validate` 命令验证配置，或查看相关服务的启动日志。

### Q: 配置后需要重启服务吗？

A: 是的，修改 `.env` 文件后需要重启相关服务才能生效。

### Q: 如何保护API密钥安全？

A: 
1. `.env` 文件已在 `.gitignore` 中，不会被提交到代码仓库
2. 设置文件权限: `chmod 600 .env`
3. 不要在公开场合分享密钥
4. 定期更换密钥

### Q: 可以使用测试密钥吗？

A: 某些服务提供沙箱环境的测试密钥，建议先使用测试密钥验证功能，再切换到生产环境密钥。

## 技术支持

如需帮助，请：
1. 查看本文档
2. 查看具体API服务的官方文档
3. 检查系统日志
4. 提交Issue到项目仓库

---

**最后更新**: 2025-11-06
**版本**: 1.0.0

