"""
业务管理API - 生产级优化
- 客户管理：客户CRUD、价值分析、订单趋势、类别升级
- 订单管理：订单查询、状态管理
- 项目管理：项目查询、状态管理

生产级特性：
- 性能监控和缓存
- 详细的日志记录
- 输入验证和清理
- 异常处理和错误日志
- 标准化响应格式
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
import sys
import time
import logging
sys.path.append('..')
from ..core.database import get_db
from modules.customer.customer_manager import CustomerManager
from modules.order.order_manager import OrderManager
from modules.project.project_manager import ProjectManager
from api.data_listener_api import data_listener

# 导入生产级工具函数
from api.middleware.performance_monitor import measure_execution_time, api_performance_monitor
from api.utils.cache_manager import cache_response
from api.utils.input_validator import validate_customer_data, validate_order_data
from api.utils.response_formatter import APIResponse

# 配置日志记录器
logger = logging.getLogger("erp_business_api")

router = APIRouter(prefix="/business", tags=["business"])


# ============ 数据模型 ============

class CustomerCreate(BaseModel):
    name: str
    code: str
    category: str = "普通"
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None


# ============ 客户管理API ============

@router.get("/customers")
@measure_execution_time
@cache_response(ttl=300)  # 5分钟缓存
async def get_customers(
    category: Optional[str] = Query(None, description="客户类别"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取客户列表 - 生产级优化"""
    with api_performance_monitor("get_customers"):
        try:
            logger.info(f"获取客户列表，类别: {category}, 关键词: {keyword}, 页码: {page}, 页大小: {page_size}")
            
            manager = CustomerManager(db)
            result = manager.list_customers(category, keyword, page, page_size)
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            logger.info(f"客户列表获取成功，共 {len(result.get('data', []))} 条记录")
            return APIResponse.success(data=result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取客户列表失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"获取客户列表失败: {str(e)}")


@router.get("/customers/{customer_id}")
@measure_execution_time
@cache_response(ttl=600)  # 10分钟缓存
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """获取客户详情 - 生产级优化"""
    with api_performance_monitor("get_customer"):
        try:
            logger.info(f"获取客户详情，客户ID: {customer_id}")
            
            # 输入验证
            if customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            manager = CustomerManager(db)
            result = manager.get_customer(customer_id)
            
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            
            logger.info(f"客户详情获取成功，客户ID: {customer_id}")
            return APIResponse.success(data=result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取客户详情失败，客户ID: {customer_id}, 错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"获取客户详情失败: {str(e)}")


@router.post("/customers")
@measure_execution_time
async def create_customer(
    customer: CustomerCreate, 
    db: Session = Depends(get_db)
):
    """创建新客户 - 生产级优化"""
    with api_performance_monitor("create_customer"):
        try:
            logger.info(f"创建新客户，客户名称: {customer.name}, 客户代码: {customer.code}")
            
            # 输入验证和清理
            validation_result = validate_customer_data(customer.dict())
            if not validation_result['success']:
                raise HTTPException(status_code=400, detail=validation_result['error'])
            
            # 清理输入数据
            cleaned_data = validation_result['cleaned_data']
            
            manager = CustomerManager(db)
            result = manager.create_customer(cleaned_data)
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            logger.info(f"客户创建成功，客户ID: {result.get('data', {}).get('id', '未知')}")
            return APIResponse.success(data=result, message="客户创建成功")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建客户失败，客户名称: {customer.name}, 错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"创建客户失败: {str(e)}")


@router.put("/customers/{customer_id}")
@measure_execution_time
async def update_customer(
    customer_id: int,
    update: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """更新客户信息 - 生产级优化"""
    with api_performance_monitor("update_customer"):
        try:
            logger.info(f"更新客户信息，客户ID: {customer_id}")
            
            # 输入验证
            if customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            # 输入验证和清理
            validation_result = validate_customer_data(update.dict(exclude_unset=True))
            if not validation_result['success']:
                raise HTTPException(status_code=400, detail=validation_result['error'])
            
            # 清理输入数据
            cleaned_data = validation_result['cleaned_data']
            
            manager = CustomerManager(db)
            result = manager.update_customer(customer_id, cleaned_data)
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            logger.info(f"客户信息更新成功，客户ID: {customer_id}")
            return APIResponse.success(data=result, message="客户信息更新成功")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新客户信息失败，客户ID: {customer_id}, 错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"更新客户信息失败: {str(e)}")


@router.delete("/customers/{customer_id}")
@measure_execution_time
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """删除客户 - 生产级优化"""
    with api_performance_monitor("delete_customer"):
        try:
            logger.info(f"删除客户，客户ID: {customer_id}")
            
            # 输入验证
            if customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            manager = CustomerManager(db)
            result = manager.delete_customer(customer_id)
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            logger.info(f"客户删除成功，客户ID: {customer_id}")
            return APIResponse.success(data=result, message="客户删除成功")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除客户失败，客户ID: {customer_id}, 错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"删除客户失败: {str(e)}")


@router.get("/customers/{customer_id}/analysis")
@measure_execution_time
@cache_response(ttl=900)  # 15分钟缓存
async def analyze_customer(customer_id: int, db: Session = Depends(get_db)):
    """客户价值分析 - 生产级优化"""
    with api_performance_monitor("analyze_customer"):
        try:
            logger.info(f"执行客户价值分析，客户ID: {customer_id}")
            
            # 输入验证
            if customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            manager = CustomerManager(db)
            result = manager.analyze_customer_value(customer_id)
            
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            
            logger.info(f"客户价值分析完成，客户ID: {customer_id}")
            return APIResponse.success(data=result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"客户价值分析失败，客户ID: {customer_id}, 错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"客户价值分析失败: {str(e)}")


@router.get("/customers/{customer_id}/trend")
@measure_execution_time
@cache_response(ttl=600)  # 10分钟缓存
async def get_customer_trend(
    customer_id: int,
    period: str = Query("month", description="分析周期: day, week, month, quarter, year"),
    db: Session = Depends(get_db)
):
    """客户订单趋势 - 生产级优化"""
    with api_performance_monitor("get_customer_trend"):
        try:
            logger.info(f"获取客户订单趋势，客户ID: {customer_id}, 周期: {period}")
            
            # 输入验证
            if customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            valid_periods = ["day", "week", "month", "quarter", "year"]
            if period not in valid_periods:
                raise HTTPException(status_code=400, detail=f"无效的周期类型: {period}")
            
            manager = CustomerManager(db)
            result = manager.get_customer_order_trend(customer_id, period)
            
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            
            logger.info(f"客户订单趋势获取成功，客户ID: {customer_id}, 数据点数量: {len(result.get('data', {}).get('trend_data', []))}")
            return APIResponse.success(data=result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取客户订单趋势失败，客户ID: {customer_id}, 错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"获取客户订单趋势失败: {str(e)}")


@router.post("/customers/{customer_id}/upgrade")
@measure_execution_time
async def upgrade_customer(
    customer_id: int,
    new_category: str,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """升级客户类别 - 生产级优化"""
    with api_performance_monitor("upgrade_customer"):
        try:
            logger.info(f"升级客户类别，客户ID: {customer_id}, 新类别: {new_category}")
            
            # 输入验证
            if customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            if not new_category.strip():
                raise HTTPException(status_code=400, detail="新类别不能为空")
            
            valid_categories = ["普通", "重要", "VIP", "战略"]
            if new_category not in valid_categories:
                raise HTTPException(status_code=400, detail=f"无效的客户类别: {new_category}")
            
            manager = CustomerManager(db)
            result = manager.upgrade_customer_category(customer_id, new_category, reason)
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            
            logger.info(f"客户类别升级成功，客户ID: {customer_id}, 新类别: {new_category}")
            return APIResponse.success(data=result, message="客户类别升级成功")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"客户类别升级失败，客户ID: {customer_id}, 错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"客户类别升级失败: {str(e)}")


# ============ 订单管理API（待实现） ============

@router.get("/orders")
@measure_execution_time
@cache_response(ttl=300)  # 5分钟缓存
async def get_orders(
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[str] = Query(None, description="订单状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取订单列表 - 生产级优化"""
    with api_performance_monitor("get_orders"):
        try:
            logger.info(f"获取订单列表，客户ID: {customer_id}, 状态: {status}, 页码: {page}, 页大小: {page_size}")
            
            # 输入验证
            if customer_id and customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            manager = OrderManager(db, data_listener=data_listener)
            result = manager.list_orders(customer_id, status, None, None, page, page_size)
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result.get('error', '获取订单列表失败'))
            
            logger.info(f"订单列表获取成功，共 {len(result.get('data', []))} 条记录")
            return APIResponse.success(data=result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取订单列表失败，错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")


# ============ 项目管理API（待实现） ============

@router.get("/projects")
@measure_execution_time
@cache_response(ttl=300)  # 5分钟缓存
async def get_projects(
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[str] = Query(None, description="项目状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取项目列表 - 生产级优化"""
    with api_performance_monitor("get_projects"):
        try:
            logger.info(f"获取项目列表，客户ID: {customer_id}, 状态: {status}, 页码: {page}, 页大小: {page_size}")
            
            # 输入验证
            if customer_id and customer_id <= 0:
                raise HTTPException(status_code=400, detail="客户ID必须为正整数")
            
            # TODO: 实现项目管理器
            result = {
                "success": True,
                "message": "项目管理功能开发中",
                "data": []
            }
            
            logger.info("项目列表获取成功（功能开发中）")
            return APIResponse.success(data=result, message="项目管理功能开发中")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取项目列表失败，错误: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")











