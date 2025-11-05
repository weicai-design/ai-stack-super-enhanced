# 🚀 AI Stack Super Enhanced - 快速开始指南

**版本**: v1.0  
**更新时间**: 2025-11-04

---

## 📋 前置条件

确保已安装：
- ✅ Python 3.13+
- ✅ Node.js 18+
- ✅ Docker
- ✅ Ollama

---

## ⚡ 5分钟快速启动

### 1. 启动ERP系统（核心功能）

```bash
cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management"
./start_erp.sh
```

**等待30秒**，然后访问:
- 📊 ERP主页: http://localhost:8012
- 💰 财务看板: http://localhost:8012/finance/dashboard

### 2. 启动其他服务

```bash
cd /Users/ywc/ai-stack-super-enhanced
./scripts/start_additional_services.sh
```

### 3. 验证系统状态

```bash
cd /Users/ywc/ai-stack-super-enhanced
source venv/bin/activate
python3 scripts/system_health_check.py
```

期望结果: **80%+的服务运行中** ✅

---

## 🌐 访问各个系统

| 系统 | 地址 | 说明 |
|------|------|------|
| 🌐 OpenWebUI | http://localhost:3000 | AI对话界面 |
| 💼 ERP前端 | http://localhost:8012 | 企业管理主页 |
| 📊 ERP API | http://localhost:8013/docs | API文档 |
| 📈 股票系统 | http://localhost:8014 | 股票交易看板 |
| 🔍 趋势分析 | http://localhost:8015 | 趋势分析 |
| 🤖 任务代理 | http://localhost:8017 | 任务管理 |
| 🛠️ 资源管理 | http://localhost:8018 | 资源监控 |
| 🧠 自我学习 | http://localhost:8019 | 学习系统 |

---

## 💡 常用操作

### 查看日志

```bash
# 查看所有日志
ls -lh /Users/ywc/ai-stack-super-enhanced/logs/

# 实时查看ERP后端日志
tail -f /tmp/erp-backend.log

# 实时查看股票系统日志
tail -f /Users/ywc/ai-stack-super-enhanced/logs/Stock.log
```

### 停止服务

```bash
# 停止ERP系统
cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management"
./stop_erp.sh

# 停止特定端口的服务
lsof -ti:8014 | xargs kill -9
```

### 重启服务

```bash
# 重启所有服务
cd /Users/ywc/ai-stack-super-enhanced
./scripts/restart_failed_services.sh
```

---

## 🎯 推荐的首次体验流程

### 1. 探索ERP系统 (10分钟)

1. 访问 http://localhost:8012
2. 点击「财务管理」→「财务看板」
3. 尝试切换不同的时间周期（日/周/月/季/年）
4. 查看「经营分析」的各个图表
5. 探索「流程管理」的16阶段可视化

### 2. 测试API接口 (5分钟)

1. 访问 http://localhost:8013/docs
2. 展开任意API接口
3. 点击「Try it out」
4. 点击「Execute」测试

### 3. 体验AI对话 (5分钟)

1. 访问 http://localhost:3000
2. 开始与AI对话
3. 尝试上传文件（如PDF、Word文档）

---

## 📱 移动端访问

在同一网络下，使用你的IP地址访问：

```bash
# 查看本机IP
ipconfig getifaddr en0

# 然后在手机浏览器访问
http://<你的IP>:8012
```

---

## ❓ 常见问题

### Q1: 页面无法打开？

**A**: 先检查服务是否运行：
```bash
curl http://localhost:8012
curl http://localhost:8013/health
```

### Q2: ERP页面是空白的？

**A**: 清除浏览器缓存：
- Mac: `Cmd + Shift + R`
- Windows: `Ctrl + Shift + R`

### Q3: API返回404错误？

**A**: 检查后端是否运行：
```bash
lsof -i:8013
tail -f /tmp/erp-backend.log
```

### Q4: 如何查看系统状态？

**A**: 运行健康检查：
```bash
cd /Users/ywc/ai-stack-super-enhanced
source venv/bin/activate
python3 scripts/system_health_check.py
```

---

## 🛠️ 故障排除

### 服务启动失败

1. 检查端口占用：
```bash
lsof -i:8012
lsof -i:8013
```

2. 查看错误日志：
```bash
tail -50 /tmp/erp-backend.log
```

3. 重启服务：
```bash
./stop_erp.sh
./start_erp.sh
```

### 前端编译错误

1. 清除node_modules：
```bash
cd web/frontend
rm -rf node_modules
npm install
```

2. 重新构建：
```bash
npm run build
npm run dev
```

---

## 📚 进阶操作

### 修改端口

编辑 `start_erp.sh`，修改：
```bash
--port 8013  # 修改为其他端口
```

### 添加测试数据

```bash
cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management"
python scripts/add_test_data.py
```

### 数据库管理

```bash
# 查看数据库
sqlite3 erp_data.db ".tables"

# 导出数据
sqlite3 erp_data.db ".dump" > backup.sql
```

---

## 🎊 下一步

1. ✅ 浏览完所有功能模块
2. ✅ 添加真实业务数据
3. ✅ 自定义报表和看板
4. ✅ 集成到现有业务流程

---

## 💬 获取帮助

- 📖 查看完整文档: `SYSTEM_STATUS_REPORT.md`
- 🐛 报告问题: 查看日志并记录错误信息
- 💡 功能建议: 记录在 `FEATURE_REQUESTS.md`

---

**祝使用愉快！** 🎉

如果遇到任何问题，请查看系统状态报告或运行健康检查工具。


