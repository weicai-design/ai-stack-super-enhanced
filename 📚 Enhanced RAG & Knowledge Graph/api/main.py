"""
股票量化API主启动文件
FastAPI应用入口点
"""

from fastapi import FastAPI
from stock_complete_api import router

# 创建FastAPI应用实例
app = FastAPI(
    title="AI股票量化交易平台",
    description="对标Bloomberg Terminal + QuantConnect的完整量化交易平台",
    version="4.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 包含API路由
app.include_router(router)

# 根路径
@app.get("/")
async def root():
    return {
        "message": "欢迎使用AI股票量化交易平台",
        "version": "4.0",
        "docs": "/docs",
        "features": [
            "📊 实时行情分析",
            "🎯 策略设计优化", 
            "📉 策略回测验证",
            "⚡ 智能自动交易",
            "🛡️ 风险全面管理",
            "💼 组合优化配置",
            "🤖 AI智能预测",
            "🔍 监控系统集成"
        ]
    }

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2025-11-09T15:53:00Z",
        "version": "4.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )