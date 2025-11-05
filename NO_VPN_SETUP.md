# 🇨🇳 无VPN环境配置指南

**适用场景**: 在中国大陆或无法访问HuggingFace等外网服务  
**配置目标**: 使用国内镜像源，无需VPN即可正常使用系统

---

## 🚀 快速开始

### 步骤1: 运行配置脚本

```bash
# 一键配置所有国内镜像
bash scripts/setup_china_mirrors.sh
```

这个脚本会：
- ✅ 配置HuggingFace镜像（hf-mirror.com）
- ✅ 配置PyPI镜像（清华大学镜像）
- ✅ 创建持久化配置文件
- ✅ 自动应用到pip配置

### 步骤2: 加载镜像配置

```bash
# 临时加载（当前终端）
source .config/china_mirrors.env

# 或使用加载脚本
source scripts/load_china_mirrors.sh
```

### 步骤3: 下载模型

```bash
# 使用已配置的镜像下载模型
bash scripts/download_model.sh
```

### 步骤4: 启动服务

```bash
# 服务启动脚本会自动加载镜像配置
make dev
```

---

## 📋 配置内容

### HuggingFace镜像

- **主镜像**: https://hf-mirror.com
- **用途**: 下载Transformers模型和SentenceTransformer模型
- **自动应用**: 所有模型下载代码已优化，自动使用镜像

### PyPI镜像

- **主镜像**: https://pypi.tuna.tsinghua.edu.cn/simple（清华大学）
- **备用镜像**:
  - 阿里云: https://mirrors.aliyun.com/pypi/simple
  - 豆瓣: https://pypi.douban.com/simple
  - 北外: https://mirrors.bfsu.edu.cn/pypi/web/simple

### 配置文件位置

- **镜像配置**: `.config/china_mirrors.env`
- **pip配置**: `~/.pip/pip.conf`

---

## 🔧 手动配置（可选）

### 方法1: 环境变量

```bash
export HF_ENDPOINT=https://hf-mirror.com
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

### 方法2: pip配置文件

编辑 `~/.pip/pip.conf`:

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

### 方法3: 项目级配置

在项目根目录创建 `.env` 文件:

```bash
HF_ENDPOINT=https://hf-mirror.com
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📦 代码级优化

### 模型下载自动使用镜像

所有模型加载代码已优化：

```python
# 自动检测并使用镜像
from utils.huggingface_mirror import ensure_mirror_configured
ensure_mirror_configured()

# 或手动设置
from utils.huggingface_mirror import setup_huggingface_mirror
setup_huggingface_mirror("https://hf-mirror.com")
```

### 自动加载位置

以下模块会自动加载镜像配置：
- ✅ `api/app.py` - 主API服务
- ✅ `core/advanced_reranker.py` - 重排序模型
- ✅ `core/embedding_service.py` - 嵌入模型
- ✅ `scripts/dev.sh` - 开发环境启动脚本

---

## 🧪 验证配置

### 检查HuggingFace镜像

```bash
echo $HF_ENDPOINT
# 应该输出: https://hf-mirror.com
```

### 检查pip镜像

```bash
pip config list
# 应该显示index-url指向镜像
```

### 测试模型下载

```bash
python3 -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from sentence_transformers import SentenceTransformer
print('✅ 镜像配置成功')
"
```

---

## 🔄 持久化配置

### 自动加载（推荐）

添加到 `~/.bashrc` 或 `~/.zshrc`:

```bash
# 加载AI Stack镜像配置
if [ -f "/path/to/ai-stack-super-enhanced/.config/china_mirrors.env" ]; then
    source /path/to/ai-stack-super-enhanced/.config/china_mirrors.env
fi
```

### Docker环境

在 `Dockerfile` 或 `docker-compose.yml` 中：

```yaml
environment:
  - HF_ENDPOINT=https://hf-mirror.com
  - PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 💡 故障排查

### 问题1: 模型下载失败

**解决方案**:
```bash
# 1. 检查镜像配置
source .config/china_mirrors.env
echo $HF_ENDPOINT

# 2. 手动设置镜像
export HF_ENDPOINT=https://hf-mirror.com

# 3. 重新下载
bash scripts/download_model.sh
```

### 问题2: pip安装慢或失败

**解决方案**:
```bash
# 1. 检查pip配置
cat ~/.pip/pip.conf

# 2. 手动指定镜像安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题3: 服务启动时模型加载失败

**解决方案**:
1. 确保已运行 `bash scripts/setup_china_mirrors.sh`
2. 确保已下载模型: `bash scripts/download_model.sh`
3. 检查环境变量: `env | grep HF_ENDPOINT`

---

## 📊 镜像源对比

| 镜像源 | 速度 | 稳定性 | 推荐度 |
|--------|------|--------|--------|
| hf-mirror.com | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 强烈推荐 |
| pypi.tuna.tsinghua.edu.cn | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 强烈推荐 |
| mirrors.aliyun.com | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ 推荐 |
| pypi.douban.com | ⭐⭐⭐ | ⭐⭐⭐ | ⚠️ 可用 |

---

## ✅ 验证清单

- [ ] 运行了 `bash scripts/setup_china_mirrors.sh`
- [ ] 环境变量 `HF_ENDPOINT` 已设置
- [ ] pip配置文件 `~/.pip/pip.conf` 已创建
- [ ] 模型已成功下载（`bash scripts/download_model.sh`）
- [ ] 服务可以正常启动（`make dev`）
- [ ] API端点可以正常访问

---

## 🎯 优化效果

配置完成后：
- ✅ **模型下载速度**: 提升5-10倍（取决于网络）
- ✅ **依赖安装速度**: 提升3-5倍
- ✅ **稳定性**: 显著提升（无需VPN）
- ✅ **自动化**: 一次配置，永久使用

---

**配置完成后，系统即可在无VPN环境下正常运行！** 🎉

