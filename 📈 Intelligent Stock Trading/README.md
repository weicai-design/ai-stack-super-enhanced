# 📈 智能股票交易系统

基于AI的智能股票交易系统，支持多策略分析和自动化交易。

---

## 🚀 快速开始

### 安装依赖
```bash
cd "/Users/ywc/ai-stack-super-enhanced/📈 Intelligent Stock Trading"
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn requests sqlalchemy
```

### 启动API服务
```bash
python api/main.py
```

**访问**: http://localhost:8014

### 查看API文档
http://localhost:8014/docs

---

## 📚 核心功能

### 1. 数据获取（需求3.1, 3.2）
- 股票列表获取
- 实时股价监控
- 历史数据查询
- 公司基本信息

### 2. 策略分析（需求3.2）
- **趋势跟踪策略**: MA均线分析
- **价值投资策略**: PE/PB估值
- **AI智能策略**: 大模型分析

### 3. 市场情绪（需求3.3）
- 情绪指数计算
- 恐惧贪婪指数
- 市场趋势判断

### 4. 策略优化（需求3.5）
- 表现记录
- 收益率统计
- 胜率计算

---

## 🎯 API端点

### 核心接口
```
GET  /api/stock/list                     获取股票列表
GET  /api/stock/price/{code}             实时价格
GET  /api/stock/history/{code}           历史数据
GET  /api/stock/analyze/{code}           策略分析
GET  /api/stock/sentiment                 市场情绪
GET  /api/stock/strategies/performance   策略表现
GET  /api/stock/dashboard                交易看板
```

---

## 📊 数据模型

### 核心表结构
- **stocks**: 股票信息
- **stock_prices**: 股价数据
- **trading_strategies**: 交易策略
- **trades**: 交易记录
- **positions**: 持仓信息
- **market_sentiment**: 市场情绪
- **strategy_performance**: 策略表现

---

## 🎨 前端界面

### 看板页面
**文件**: `web/templates/dashboard.html`

**功能**:
- 总资产统计
- 总收益显示
- 收益率计算
- 市场情绪指标
- 持仓分布饼图
- 持仓股票列表

---

## 🔧 技术栈

- **后端**: FastAPI
- **数据库**: SQLAlchemy
- **图表**: ECharts
- **AI**: Ollama + Qwen2.5

---

## 📝 使用示例

### 获取股票列表
```bash
curl http://localhost:8014/api/stock/list
```

### 获取实时价格
```bash
curl http://localhost:8014/api/stock/price/600519
```

### 策略分析
```bash
curl http://localhost:8014/api/stock/analyze/600519
```

### 市场情绪
```bash
curl http://localhost:8014/api/stock/sentiment
```

---

## 🎯 已实现的用户需求

- ✅ 3.1 API接入框架
- ✅ 3.2 AI策略制定
- ✅ 3.3 市场情绪分析
- ⏳ 3.4 自动买卖（框架完成）
- ✅ 3.5 策略优化和收益率
- ⏳ 3.6 信息预处理（待集成）
- ⏳ 3.7 自我学习进化（框架完成）
- ⏳ 3.8 RAG关联（待集成）
- ⏳ 3.9 OpenWebUI关联（待集成）
- ⏳ 3.10 Docker部署（待配置）

---

## 🚀 下一步开发

### 短期（本周）
- 对接真实股票数据API
- 完善前端Vue应用
- 添加K线图展示

### 中期（下周）
- 实现自动交易执行
- 与RAG系统集成
- 与OpenWebUI集成

---

**版本**: v1.0.0  
**状态**: ✅ 基础功能可用  
**完成度**: 60%

