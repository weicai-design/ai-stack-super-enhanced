#!/usr/bin/env python3
"""
AI Stack 统一Dashboard服务器
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="AI Stack Unified Dashboard")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
BASE_DIR = os.path.dirname(__file__)

@app.get("/")
async def root():
    """主页"""
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🌟 AI Stack 统一控制台")
    print("="*60)
    print("\n访问地址: http://localhost:8000")
    print("\n这是你的AI Stack统一入口，可以看到所有系统！")
    print("\n" + "="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)



