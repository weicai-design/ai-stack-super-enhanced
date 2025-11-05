# 🚀 快速开始指南

欢迎使用 AI Stack Super Enhanced！本指南将帮助你在5分钟内启动并运行整个系统。

---

## ⚡ 超快速启动（1分钟）

```bash
# 1. 进入项目目录
cd /Users/ywc/ai-stack-super-enhanced

# 2. 一键启动所有服务
./scripts/start_all_services.sh

# 3. 等待30秒后测试
sleep 30 && ./scripts/test_all_systems.sh
```

**就这么简单！** ✅

---

## 🌐 访问系统

### 核心系统
- **ERP系统**: http://localhost:8012
- **OpenWebUI**: http://localhost:3000

### API服务
- **RAG API**: http://localhost:8011/docs
- **ERP API**: http://localhost:8013/docs
- **股票API**: http://localhost:8014/docs
- **趋势API**: http://localhost:8015/docs
- **内容API**: http://localhost:8016/docs
- **任务API**: http://localhost:8017/docs
- **资源API**: http://localhost:8018/docs
- **学习API**: http://localhost:8019/docs

---

## 📋 推荐使用顺序

### 第1步：访问ERP系统（最完整）
```bash
open http://localhost:8012
```

**可以做什么**:
- ✅ 查看财务看板（日/周/月/季/年）
- ✅ 查看经营分析（开源/成本/效益）
- ✅ 查看流程管理（16阶段可视化）
- ✅ 管理客户、订单、项目

**演示数据已准备好！**

---

### 第2步：探索OpenWebUI
```bash
open http://localhost:3000
```

**可以做什么**:
- 💬 与AI聊天
- 📚 使用RAG知识检索
- 💼 查询ERP数据
- 📂 上传文件处理

---

### 第3步：测试API接口
```bash
# 访问任意服务的API文档
open http://localhost:8013/docs  # ERP API
open http://localhost:8017/docs  # 任务代理API
open http://localhost:8018/docs  # 资源管理API
```

**可以做什么**:
- 📡 查看所有API接口
- 🧪 直接测试API
- 📖 查看详细文档

---

## 🛠️ 常用命令

### 启动服务
```bash
# 启动所有服务
./scripts/start_all_services.sh

# 或使用Docker
docker-compose -f docker-compose.full.yml up -d
```

### 测试服务
```bash
# 测试所有服务是否运行
./scripts/test_all_systems.sh

# 测试特定服务
curl http://localhost:8013/health
```

### 停止服务
```bash
# 停止所有服务
./scripts/stop_all_services.sh

# 或停止Docker
docker-compose -f docker-compose.full.yml down
```

### 查看日志
```bash
# 查看所有日志
ls -la logs/

# 查看特定服务日志
tail -f logs/ERP-Backend.log
tail -f logs/Task-Agent.log
```

---

## 🎯 使用场景示例

### 场景1：财务分析
1. 打开 http://localhost:8012
2. 点击"财务看板"
3. 选择时间范围（日/周/月/季/年）
4. 查看收入、支出、利润趋势

### 场景2：经营决策
1. 打开 http://localhost:8012
2. 点击"经营分析"
3. 查看"开源分析"、"成本分析"、"效益分析"
4. 获得经营建议

### 场景3：任务管理
1. 访问 http://localhost:8017/docs
2. 使用 POST /api/tasks/create 创建任务
3. 使用 POST /api/tasks/{id}/execute 执行任务
4. 使用 GET /api/tasks/monitoring/active 监控进度

### 场景4：资源监控
1. 访问 http://localhost:8018/docs
2. 使用 GET /api/resources/system 查看系统资源
3. 使用 GET /api/resources/conflicts/detect 检测冲突
4. 使用 POST /api/resources/conflicts/resolve 解决冲突

---

## 🔧 故障排除

### 问题1：服务启动失败

**解决方案**:
```bash
# 1. 检查端口占用
lsof -i :8013

# 2. 停止所有服务
./scripts/stop_all_services.sh

# 3. 重新启动
./scripts/start_all_services.sh

# 4. 查看日志
tail -f logs/*.log
```

### 问题2：页面无法访问

**解决方案**:
```bash
# 1. 确认服务运行
./scripts/test_all_systems.sh

# 2. 清除浏览器缓存
# Mac: Cmd + Shift + R
# Windows: Ctrl + Shift + R

# 3. 使用无痕模式
# Mac: Cmd + Shift + N
# Windows: Ctrl + Shift + N
```

### 问题3：Docker无法启动

**解决方案**:
```bash
# 1. 检查Docker状态
docker ps

# 2. 如果Docker未运行
open -a Docker

# 3. 等待Docker启动
sleep 15

# 4. 重试
./scripts/start_all_services.sh
```

---

## 📊 系统状态检查

### 快速检查
```bash
# 运行测试脚本
./scripts/test_all_systems.sh
```

### 详细检查
```bash
# 检查所有端口
for port in 3000 8011 8012 8013 8014 8015 8016 8017 8018 8019; do
    echo "Port $port:"
    lsof -i :$port
    echo "---"
done
```

### 服务健康检查
```bash
# ERP后端
curl http://localhost:8013/health

# 任务代理
curl http://localhost:8017/health

# 资源管理
curl http://localhost:8018/health
```

---

## 💡 高级使用

### 自定义配置

编辑各服务的配置文件：
```bash
# ERP配置
vi "💼 Intelligent ERP & Business Management/config.py"

# 任务代理配置
vi "🤖 Intelligent Task Agent/config.py"
```

### 添加测试数据
```bash
# 添加ERP测试数据
cd "💼 Intelligent ERP & Business Management"
python scripts/add_test_data.py
python scripts/add_business_test_data.py
```

### 开发模式
```bash
# 单独启动某个服务（开发模式）
cd "💼 Intelligent ERP & Business Management"
source venv/bin/activate
python -m uvicorn api.main:app --reload
```

---

## 📱 移动端访问

如果你的Mac在同一网络下：
```bash
# 1. 获取Mac的IP地址
ipconfig getifaddr en0

# 2. 在移动设备访问
# 将 localhost 替换为 Mac的IP
# 例如: http://192.168.1.100:8012
```

---

## 🔐 安全建议

### 开发环境（当前）
- ✅ 可以使用默认配置
- ✅ 无需认证
- ✅ 本地访问

### 生产环境（未来）
- 🔒 添加用户认证
- 🔒 使用HTTPS
- 🔒 配置防火墙
- 🔒 定期备份数据

---

## 📈 性能优化

### 如果系统运行慢

1. **增加资源分配**:
```bash
# 访问资源管理API
curl http://localhost:8018/api/resources/system
```

2. **关闭不需要的服务**:
```bash
# 只启动需要的服务
# 编辑 start_all_services.sh，注释掉不需要的服务
```

3. **使用缓存**:
- Redis已在Docker配置中
- 可以启用Redis缓存加速

---

## 🎓 学习资源

### 文档
- [完整文档](./README.md)
- [开发报告](./🎯最终开发成果总结.md)
- [各系统README](./*/README.md)

### API文档
- 每个服务的 `/docs` 路径都有完整API文档

### 示例代码
- 查看各系统的 `tests/` 目录
- 查看 `scripts/` 目录的脚本

---

## 🤝 获取帮助

### 查看日志
```bash
# 所有日志在这里
ls -la logs/

# 实时查看日志
tail -f logs/<service>.log
```

### 常见问题
1. **端口被占用**: 使用 `stop_all_services.sh` 停止服务
2. **页面加载慢**: 清除浏览器缓存
3. **服务启动失败**: 查看对应的日志文件

---

## 🎉 开始探索！

**推荐探索路径**:
1. ✅ 访问ERP系统看板（最完整）
2. ✅ 尝试OpenWebUI聊天
3. ✅ 浏览各API文档
4. ✅ 测试创建任务
5. ✅ 查看资源监控

**祝你使用愉快！** 🚀

---

## 📞 快速参考

### 一键命令
```bash
# 启动
./scripts/start_all_services.sh

# 测试
./scripts/test_all_systems.sh

# 停止
./scripts/stop_all_services.sh
```

### 主要地址
- **ERP**: http://localhost:8012
- **OpenWebUI**: http://localhost:3000
- **API文档**: http://localhost:8013/docs

### 日志位置
- `/Users/ywc/ai-stack-super-enhanced/logs/`

---

**快速开始就是这么简单！** ✅

**现在就开始探索吧！** 🚀


