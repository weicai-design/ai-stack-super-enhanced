"""
静态文件路由
Static File Routes
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

@router.get("/")
async def index():
    """首页"""
    html_path = os.path.join(BASE_DIR, "web", "templates", "enhanced_dashboard.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        # 返回原始dashboard
        html_path = os.path.join(BASE_DIR, "web", "templates", "dashboard.html")
        return FileResponse(html_path)

@router.get("/dashboard")
async def dashboard():
    """仪表盘"""
    html_path = os.path.join(BASE_DIR, "web", "templates", "enhanced_dashboard.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        html_path = os.path.join(BASE_DIR, "web", "templates", "dashboard.html")
        return FileResponse(html_path)



