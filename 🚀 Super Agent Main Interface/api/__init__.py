"""
超级Agent主界面API模块
"""

# 延迟导入router以避免相对导入问题
def get_router():
    """获取主路由器实例"""
    try:
        from .super_agent_api import router
        return router
    except ImportError:
        # 如果导入失败，返回一个空的APIRouter
        from fastapi import APIRouter
        return APIRouter()

router = get_router()

__all__ = ['router', 'get_router']

