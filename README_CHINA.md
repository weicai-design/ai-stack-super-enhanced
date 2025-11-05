# 🇨🇳 AI Stack Super Enhanced - 国内使用指南（无VPN）

**适用环境**: 中国大陆或无法访问外网服务  
**优化目标**: 完全无需VPN即可使用所有功能

---

## 🚀 快速开始（3步）

### 步骤1: 配置国内镜像（一键完成）

```bash
bash scripts/setup_china_mirrors.sh
```

✅ 自动配置：
- HuggingFace镜像（hf-mirror.com）
- PyPI镜像（清华大学）
- pip配置
- 环境变量

### 步骤2: 安装依赖（使用镜像）

```bash
bash requirements_install_china.sh
```

或手动：

```bash
source .config/china_mirrors.env
pip install -r requirements.txt
```

### 步骤3: 下载模型（使用镜像）

```bash
bash scripts/download_model.sh
```

---

## 📋 详细配置说明

### 1. 镜像配置

运行配置脚本后，系统会自动：

- ✅ 创建 `.config/china_mirrors.env` 配置文件
- ✅ 更新 `~/.pip/pip.conf` pip配置
- ✅ 设置 `HF_ENDPOINT` 环境变量
- ✅ 配置git镜像（可选）

### 2. 模型下载

所有模型下载代码已优化，自动使用国内镜像：

```python
# 代码自动检测并使用镜像
from utils.huggingface_mirror import ensure_mirror_configured
ensure_mirror_configured()
```

支持的模型：
- ✅ all-MiniLM-L6-v2（默认，87MB）
- ✅ bge-reranker-large（高级重排序，可选）
- ✅ 其他SentenceTransformer模型

### 3. 服务启动

启动脚本会自动加载镜像配置：

```bash
make dev
```

服务会：
- ✅ 自动加载镜像配置
- ✅ 优先使用本地模型
- ✅ 如果本地没有，从镜像下载

---

## 🔧 代码级优化

### 已优化的模块

以下模块已自动使用国内镜像：

1. **api/app.py** - 主API服务（模型加载）
2. **core/advanced_reranker.py** - 重排序模型
3. **core/embedding_service.py** - 嵌入模型
4. **scripts/dev.sh** - 开发环境启动
5. **scripts/download_model.sh** - 模型下载

### 自动降级策略

如果网络请求失败：
- ✅ 自动重试（最多3次，指数退避）
- ✅ 使用降级值（如果配置）
- ✅ 详细错误日志
- ✅ 友好的错误提示

---

## 📦 离线安装（可选）

如果需要完全离线安装：

### 在有网络的机器上准备离线包

```bash
# 使用国内镜像下载所有依赖
bash scripts/prepare_offline_bundle.sh
```

这会创建 `offline_bundle.tar.gz`，包含：
- 所有Python包（wheels）
- 可选：模型文件

### 在离线机器上安装

```bash
# 传输 offline_bundle.tar.gz 到目标机器
# 然后运行
bash scripts/offline_install.sh
```

---

## 🐳 Docker部署（无VPN）

### 使用Docker Compose

```bash
# 1. 配置镜像（宿主机）
bash scripts/setup_china_mirrors.sh

# 2. 启动服务（自动使用镜像）
docker-compose -f docker-compose.rag.yml up -d
```

Docker配置已优化：
- ✅ 环境变量自动设置镜像
- ✅ pip使用国内镜像安装依赖
- ✅ 模型自动从镜像下载

### 手动构建镜像

```bash
# 构建时会自动使用镜像
docker build -t ai-stack-enhanced:latest .
```

---

## 🔍 验证配置

### 检查镜像配置

```bash
# 检查环境变量
echo $HF_ENDPOINT
# 应该输出: https://hf-mirror.com

# 检查pip配置
pip config list
# 应该显示清华大学镜像

# 检查配置文件
cat .config/china_mirrors.env
```

### 测试模型下载

```bash
python3 -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from sentence_transformers import SentenceTransformer
print('✅ 镜像配置成功，可以下载模型')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(f'✅ 模型下载成功，维度: {model.get_sentence_embedding_dimension()}')
"
```

---

## 💡 常见问题

### Q1: 模型下载失败怎么办？

**A**: 
1. 检查镜像配置：`echo $HF_ENDPOINT`
2. 手动设置：`export HF_ENDPOINT=https://hf-mirror.com`
3. 重新下载：`bash scripts/download_model.sh`

### Q2: pip安装很慢或失败？

**A**:
1. 检查pip配置：`cat ~/.pip/pip.conf`
2. 手动指定镜像：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
   ```

### Q3: 服务启动时模型加载失败？

**A**:
1. 确保已配置镜像：`bash scripts/setup_china_mirrors.sh`
2. 确保模型已下载：`bash scripts/download_model.sh`
3. 检查环境变量：`env | grep HF_ENDPOINT`

### Q4: 如何切换镜像源？

**A**: 编辑 `.config/china_mirrors.env`，修改 `HF_ENDPOINT` 和 `PIP_INDEX_URL`

---

## 📊 性能对比

| 操作 | 使用VPN | 使用国内镜像 | 提升 |
|------|---------|-------------|------|
| 模型下载 | 5-10分钟 | 1-3分钟 | **3-5倍** |
| 依赖安装 | 10-20分钟 | 2-5分钟 | **3-4倍** |
| 网络稳定性 | 不稳定 | 稳定 | **显著提升** |

---

## ✅ 验证清单

配置完成后，检查：

- [ ] 运行了 `bash scripts/setup_china_mirrors.sh`
- [ ] `HF_ENDPOINT` 环境变量已设置
- [ ] pip配置文件已创建
- [ ] 模型已成功下载
- [ ] 依赖已成功安装
- [ ] 服务可以正常启动
- [ ] API端点可以正常访问

---

## 🎯 完整示例

```bash
# 1. 配置镜像
bash scripts/setup_china_mirrors.sh

# 2. 安装依赖
source .config/china_mirrors.env
bash requirements_install_china.sh

# 3. 下载模型
bash scripts/download_model.sh

# 4. 启动服务
make dev

# 5. 验证服务
curl http://127.0.0.1:8011/readyz
```

---

## 📚 相关文档

- **详细配置指南**: `NO_VPN_SETUP.md`
- **离线安装指南**: `scripts/OFFLINE_README.md`
- **部署文档**: `Dockerfile`, `docker-compose.rag.yml`

---

**配置完成后，系统即可在无VPN环境下全功能运行！** 🎉

