"""
弹窗通知系统API
支持各种类型的通知和弹窗管理
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v5/notification", tags=["通知弹窗系统"])


# ==================== 数据模型 ====================

class Notification(BaseModel):
    """通知模型"""
    id: Optional[str] = None
    type: str  # info, warning, error, success
    title: str
    message: str
    priority: int = 1  # 1-5，5最高
    auto_close: bool = True
    duration: int = 3000  # 毫秒
    actions: Optional[List[dict]] = None
    created_at: Optional[str] = None
    read: bool = False


class NotificationCreate(BaseModel):
    """创建通知请求"""
    type: str
    title: str
    message: str
    priority: int = 1
    auto_close: bool = True
    duration: int = 3000


# ==================== 内存存储（生产环境应使用数据库） ====================

notifications_db = []


# ==================== API端点 ====================

@router.post("/create")
async def create_notification(notification: NotificationCreate):
    """
    创建新通知
    
    支持的类型:
    - info: 信息提示
    - warning: 警告提示
    - error: 错误提示
    - success: 成功提示
    """
    notif = Notification(
        id=str(uuid.uuid4()),
        type=notification.type,
        title=notification.title,
        message=notification.message,
        priority=notification.priority,
        auto_close=notification.auto_close,
        duration=notification.duration,
        created_at=datetime.now().isoformat()
    )
    
    notifications_db.append(notif.dict())
    
    return {
        "success": True,
        "notification_id": notif.id,
        "message": "通知已创建"
    }


@router.get("/list")
async def get_notifications(
    type: Optional[str] = None,
    read: Optional[bool] = None,
    limit: int = 50
):
    """
    获取通知列表
    
    Args:
        type: 通知类型过滤
        read: 是否已读过滤
        limit: 返回数量限制
    """
    filtered = notifications_db.copy()
    
    if type:
        filtered = [n for n in filtered if n['type'] == type]
    
    if read is not None:
        filtered = [n for n in filtered if n['read'] == read]
    
    # 按优先级和时间排序
    filtered.sort(key=lambda x: (-x['priority'], x['created_at']), reverse=True)
    
    return {
        "success": True,
        "total": len(filtered),
        "unread": len([n for n in filtered if not n['read']]),
        "notifications": filtered[:limit]
    }


@router.post("/mark-read/{notification_id}")
async def mark_as_read(notification_id: str):
    """标记通知为已读"""
    for notif in notifications_db:
        if notif['id'] == notification_id:
            notif['read'] = True
            return {
                "success": True,
                "message": "已标记为已读"
            }
    
    raise HTTPException(status_code=404, detail="通知不存在")


@router.post("/mark-all-read")
async def mark_all_read():
    """标记所有通知为已读"""
    count = 0
    for notif in notifications_db:
        if not notif['read']:
            notif['read'] = True
            count += 1
    
    return {
        "success": True,
        "marked_count": count,
        "message": f"已标记{count}条通知为已读"
    }


@router.delete("/delete/{notification_id}")
async def delete_notification(notification_id: str):
    """删除通知"""
    global notifications_db
    original_len = len(notifications_db)
    notifications_db = [n for n in notifications_db if n['id'] != notification_id]
    
    if len(notifications_db) < original_len:
        return {
            "success": True,
            "message": "通知已删除"
        }
    
    raise HTTPException(status_code=404, detail="通知不存在")


@router.delete("/clear")
async def clear_all_notifications():
    """清空所有通知"""
    global notifications_db
    count = len(notifications_db)
    notifications_db = []
    
    return {
        "success": True,
        "cleared_count": count,
        "message": f"已清空{count}条通知"
    }


@router.get("/stats")
async def get_notification_stats():
    """获取通知统计"""
    total = len(notifications_db)
    unread = len([n for n in notifications_db if not n['read']])
    
    by_type = {}
    for notif in notifications_db:
        t = notif['type']
        by_type[t] = by_type.get(t, 0) + 1
    
    return {
        "success": True,
        "total": total,
        "unread": unread,
        "read": total - unread,
        "by_type": by_type,
        "by_priority": {
            "high": len([n for n in notifications_db if n['priority'] >= 4]),
            "medium": len([n for n in notifications_db if 2 <= n['priority'] < 4]),
            "low": len([n for n in notifications_db if n['priority'] < 2])
        }
    }


@router.post("/system/notify")
async def system_notify(
    title: str,
    message: str,
    type: str = "info",
    priority: int = 3
):
    """
    系统通知快捷接口
    
    用于系统内部快速发送通知
    """
    notif = NotificationCreate(
        type=type,
        title=title,
        message=message,
        priority=priority
    )
    
    return await create_notification(notif)


# ==================== 健康检查 ====================

@router.get("/health")
async def notification_health():
    """通知系统健康检查"""
    return {
        "status": "healthy",
        "service": "notification",
        "version": "5.1.0",
        "total_notifications": len(notifications_db),
        "unread": len([n for n in notifications_db if not n['read']])
    }


if __name__ == "__main__":
    print("✅ 弹窗通知系统API已加载")
    print("📋 支持功能:")
    print("  • 创建通知")
    print("  • 获取通知列表")
    print("  • 标记已读")
    print("  • 删除通知")
    print("  • 统计分析")
    print("  • 系统快捷通知")


