"""
备忘录系统API服务器
临时启动文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 创建FastAPI应用
app = FastAPI(
    title="备忘录系统API",
    description="AI-STACK 备忘录系统后端服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 引入备忘录API路由
try:
    from api.memo_api import router as memo_router
    app.include_router(memo_router)
    print("✅ 备忘录API路由加载成功")
except Exception as e:
    print(f"⚠️  备忘录API路由加载失败: {e}")

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "备忘录系统API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "memo_api": "/api/v1/memos"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "service": "memo-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
