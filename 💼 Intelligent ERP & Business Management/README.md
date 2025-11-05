# 💼 智能ERP系统

**版本**: v1.0.0  
**开发时间**: 2025-11-03  
**状态**: ✅ 可正式使用

---

## 🚀 快速启动

### 一键启动（推荐）⭐

```bash
cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management"
./start_erp.sh
```

**自动完成**:
- ✅ 清理旧服务
- ✅ 启动后端API（端口8013）
- ✅ 启动前端Web（端口8012）
- ✅ 打开浏览器

### 停止服务

```bash
./stop_erp.sh
```

---

## 🌐 访问地址

### 主要入口
- **首页**: http://localhost:8012
- **API文档**: http://localhost:8013/docs

### 功能模块
| 模块 | 地址 |
|------|------|
| 财务看板 | http://localhost:8012/finance/dashboard |
| 财务数据 | http://localhost:8012/finance/data |
| 开源分析 | http://localhost:8012/analytics/revenue |
| 成本分析 | http://localhost:8012/analytics/cost |
| 产出效益 | http://localhost:8012/analytics/output |
| 流程列表 | http://localhost:8012/process/list |
| 流程跟踪 | http://localhost:8012/process/tracking |
| 异常监控 | http://localhost:8012/process/exceptions |
| 客户管理 | http://localhost:8012/business/customers |
| 订单管理 | http://localhost:8012/business/orders |
| 项目管理 | http://localhost:8012/business/projects |

---

## 📦 系统功能

### ✅ 财务管理（100%）
- 财务看板（日/周/月/季/年）
- 收入、支出、利润、资产统计
- 趋势图表和数据明细
- 财务数据CRUD

### ✅ 经营分析（90%）
- 开源分析（客户、订单、产品）
- 成本分析（费用、盈亏平衡）
- 产出效益（投入产出比、ROI、AI建议）

### ✅ 流程管理（85%）
- 16阶段标准流程
- 流程进度可视化
- 时间线跟踪
- 异常监控和闭环改进

### ✅ 业务管理（80%）
- 客户管理（8个测试客户）
- 订单管理（268个测试订单）
- 项目管理（3个测试项目）

---

## 🎨 界面特色

- 🎨 现代化渐变色设计
- 📊 15个ECharts专业图表
- 🔄 流畅的动画效果
- 📱 完全响应式布局
- ⚡ 快速加载和渲染

---

## 🔧 技术栈

### 前端
- Vue 3.4+ (Composition API)
- Element Plus 2.5+
- ECharts 5.5+
- Vite 5.0+

### 后端
- FastAPI 0.120.4
- SQLAlchemy 2.0.44
- SQLite / PostgreSQL
- Uvicorn 0.38.0

---

## 📊 测试数据

系统已预置测试数据：
- ✅ 62条财务数据（30天）
- ✅ 8个客户（VIP、普通、新客户）
- ✅ 268个订单（6个月）
- ✅ 3个项目
- ✅ 5个流程实例
- ✅ 3个流程异常

---

## 🐛 故障排查

### 如果页面打不开

1. **检查服务是否运行**
   ```bash
   lsof -i :8012  # 前端
   lsof -i :8013  # 后端
   ```

2. **重新启动服务**
   ```bash
   ./stop_erp.sh   # 停止
   ./start_erp.sh  # 启动
   ```

3. **查看错误日志**
   ```bash
   tail -f /tmp/erp-frontend.log  # 前端日志
   tail -f /tmp/erp-backend.log   # 后端日志
   ```

### 常见问题

- **端口被占用**: 运行 `./stop_erp.sh` 清理
- **依赖缺失**: `npm install` 或 `pip install -r requirements.txt`
- **数据库错误**: 运行数据脚本重新创建

---

## 📖 详细文档

- `服务启动指南.md` - 详细的启动和故障排查
- `ERP系统开发完成报告.md` - 完整功能说明
- `UI界面展示.md` - 界面设计文档
- `web/frontend/README.md` - 前端开发文档

---

## 🎯 系统完成度

| 模块 | 完成度 |
|------|--------|
| 财务管理 | 100% ✅ |
| 经营分析 | 90% ✅ |
| 流程管理 | 85% ✅ |
| 业务管理 | 80% ✅ |
| **总体** | **90%** ✅ |

---

## 📞 获取帮助

如有问题：
1. 查看 `服务启动指南.md`
2. 检查日志文件
3. 访问API文档查看接口

---

**项目路径**: `/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management`

**快速启动**: `./start_erp.sh`  
**停止服务**: `./stop_erp.sh`

**🎉 享受使用智能ERP系统！**

