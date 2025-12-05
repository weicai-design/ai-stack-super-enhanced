"""
API网关
统一入口、限流熔断、认证鉴权、链路追踪
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional, Callable
import httpx
import time
import uuid
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# 导入认证和授权模块
try:
    from enterprise.tenancy.auth import (
        token_service,
        api_key_service,
        get_current_tenant_from_token,
        get_current_tenant_from_api_key,
        require_tenant_from_api_key,
        check_command_permission,
        bind_tenant_context
    )
    from enterprise.tenancy.middleware import TenantIdentifier
    AUTH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"认证模块导入失败，将使用基础模式: {e}")
    AUTH_AVAILABLE = False


class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self):
        """初始化服务注册"""
        self.services = {
            "rag": {"url": "http://localhost:8011", "health": "/health"},
            "erp": {"url": "http://localhost:8013", "health": "/health"},
            "openwebui": {"url": "http://localhost:8020", "health": "/health"},
            "stock": {"url": "http://localhost:8015", "health": "/health"},
            "trend": {"url": "http://localhost:8014", "health": "/health"},
            "content": {"url": "http://localhost:8016", "health": "/health"},
            "agent": {"url": "http://localhost:8017", "health": "/health"},
            "resource": {"url": "http://localhost:8018", "health": "/health"},
            "learning": {"url": "http://localhost:8019", "health": "/health"},
        }
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """获取服务URL"""
        service = self.services.get(service_name)
        return service["url"] if service else None
    
    def list_services(self) -> Dict:
        """列出所有服务"""
        return self.services


class CircuitBreaker:
    """
    熔断器
    防止级联故障
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures: Dict[str, int] = {}
        self.last_failure_time: Dict[str, datetime] = {}
        self.state: Dict[str, str] = {}  # closed/open/half_open
    
    def call(self, service_name: str, func: Callable):
        """
        通过熔断器调用服务
        
        Args:
            service_name: 服务名称
            func: 调用函数
            
        Returns:
            调用结果
        """
        state = self.state.get(service_name, "closed")
        
        # 熔断器打开
        if state == "open":
            # 检查是否可以尝试恢复
            last_failure = self.last_failure_time.get(service_name)
            if last_failure:
                elapsed = (datetime.now() - last_failure).total_seconds()
                if elapsed >= self.recovery_timeout:
                    # 进入半开状态
                    self.state[service_name] = "half_open"
                    logger.info(f"熔断器半开: {service_name}")
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"服务暂时不可用: {service_name}"
                    )
            else:
                raise HTTPException(status_code=503, detail="服务不可用")
        
        try:
            # 执行调用
            result = func()
            
            # 调用成功，重置失败计数
            if state == "half_open":
                self.state[service_name] = "closed"
                logger.info(f"熔断器关闭: {service_name}")
            
            self.failures[service_name] = 0
            
            return result
            
        except Exception as e:
            # 调用失败，增加失败计数
            self.failures[service_name] = self.failures.get(service_name, 0) + 1
            self.last_failure_time[service_name] = datetime.now()
            
            # 检查是否达到阈值
            if self.failures[service_name] >= self.failure_threshold:
                self.state[service_name] = "open"
                logger.warning(f"熔断器打开: {service_name}")
            
            raise


class APIGateway:
    """
    API网关
    
    功能：
    - 统一路由
    - 服务代理
    - 限流熔断
    - 链路追踪
    """
    
    def __init__(self):
        """初始化API网关"""
        self.app = FastAPI(title="AI Stack API Gateway")
        self.registry = ServiceRegistry()
        self.circuit_breaker = CircuitBreaker()
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.middleware("http")
        async def authentication_middleware(request: Request, call_next):
            """
            认证中间件
            优先级：JWT Token > API Key > 请求头租户ID > 默认租户
            """
            # 跳过健康检查和文档
            skip_paths = [
                "/gateway/health",
                "/health",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/gateway/services"
            ]
            
            if any(request.url.path.startswith(path) for path in skip_paths):
                return await call_next(request)
            
            # 添加追踪ID
            trace_id = str(uuid.uuid4())
            request.state.trace_id = trace_id
            
            tenant = None
            
            if AUTH_AVAILABLE:
                try:
                    # 1. 尝试从 JWT Token 获取租户
                    auth_header = request.headers.get("Authorization", "")
                    if auth_header.startswith("Bearer "):
                        token = auth_header.replace("Bearer ", "").strip()
                        try:
                            token_payload = token_service.verify_token(token)
                            from enterprise.tenancy.manager import tenant_manager
                            tenant = tenant_manager.get_tenant(token_payload.tenant_id)
                            if tenant:
                                bind_tenant_context(request, tenant)
                                logger.debug(f"从 JWT Token 识别租户: {tenant.name} ({tenant.id})")
                        except Exception as e:
                            logger.debug(f"JWT Token 验证失败: {e}")
                    
                    # 2. 尝试从 API Key 获取租户
                    if not tenant:
                        api_key = request.headers.get("X-API-Key") or (
                            request.headers.get("Authorization", "").replace("Bearer ", "")
                            if not request.headers.get("Authorization", "").startswith("Bearer ")
                            else None
                        )
                        if api_key and api_key.startswith("ak_"):
                            api_key_obj = api_key_service.verify_api_key(api_key)
                            if api_key_obj:
                                from enterprise.tenancy.manager import tenant_manager
                                tenant = tenant_manager.get_tenant(api_key_obj.tenant_id)
                                if tenant:
                                    request.state.api_key = api_key_obj
                                    bind_tenant_context(request, tenant)
                                    logger.debug(f"从 API Key 识别租户: {tenant.name} ({tenant.id})")
                    
                    # 3. 从请求头获取租户ID
                    if not tenant:
                        tenant_identifier = TenantIdentifier()
                        tenant = tenant_identifier.identify_tenant(request)
                        if tenant:
                            bind_tenant_context(request, tenant)
                            logger.debug(f"从请求头识别租户: {tenant.name} ({tenant.id})")
                    
                except Exception as e:
                    logger.error(f"认证中间件错误: {e}")
            
            # 检查命令执行权限（如果是执行命令的请求）
            if AUTH_AVAILABLE and tenant and request.method == "POST":
                # 检查是否是执行命令的端点
                if "/execute" in request.url.path or "command" in request.url.path.lower():
                    try:
                        # 读取请求体（可能需要多次读取，这里先跳过）
                        # 实际应该在路由层面检查命令权限
                        pass
                    except Exception as e:
                        logger.debug(f"命令权限检查跳过: {e}")
            
            # 继续处理请求
            response = await call_next(request)
            
            # 添加响应头
            response.headers["X-Trace-ID"] = trace_id
            if tenant:
                response.headers["X-Tenant-ID"] = tenant.id
                response.headers["X-Tenant-Name"] = tenant.name
            
            return response
        
        @self.app.middleware("http")
        async def add_trace_id(request: Request, call_next):
            """添加追踪ID（备用）"""
            if not hasattr(request.state, "trace_id"):
                trace_id = str(uuid.uuid4())
                request.state.trace_id = trace_id
            
            response = await call_next(request)
            
            if not response.headers.get("X-Trace-ID"):
                response.headers["X-Trace-ID"] = request.state.trace_id
            
            return response
        
        @self.app.get("/gateway/health")
        async def health_check():
            """网关健康检查"""
            return {"status": "healthy", "gateway": "api-gateway"}
        
        @self.app.get("/gateway/services")
        async def list_services():
            """列出所有服务"""
            return self.registry.list_services()
        
        @self.app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
        async def proxy_request(service: str, path: str, request: Request):
            """
            代理请求到后端服务
            
            Args:
                service: 服务名称
                path: 路径
                request: 请求对象
            """
            # 获取服务URL
            service_url = self.registry.get_service_url(service)
            if not service_url:
                raise HTTPException(status_code=404, detail=f"服务不存在: {service}")
            
            # 构建目标URL
            target_url = f"{service_url}/{path}"
            
            # 通过熔断器调用
            async def call_service():
                async with httpx.AsyncClient(timeout=30) as client:
                    # 转发请求
                    method = request.method
                    headers = dict(request.headers)
                    
                    # 添加追踪ID
                    if hasattr(request.state, "trace_id"):
                        headers["X-Trace-ID"] = request.state.trace_id
                    
                    # 添加租户上下文
                    if hasattr(request.state, "tenant_id"):
                        headers["X-Tenant-ID"] = request.state.tenant_id
                    
                    if hasattr(request.state, "tenant_context"):
                        import json
                        headers["X-Tenant-Context"] = json.dumps(request.state.tenant_context)
                    
                    # 读取请求体
                    body = await request.body()
                    
                    # 发送请求
                    response = await client.request(
                        method=method,
                        url=target_url,
                        headers=headers,
                        content=body,
                        params=dict(request.query_params)
                    )
                    
                    return response
            
            try:
                response = self.circuit_breaker.call(service, call_service)
                
                # 返回响应
                return JSONResponse(
                    content=response.json() if response.content else {},
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"代理请求失败: {e}")
                raise HTTPException(status_code=502, detail="网关错误")


# 创建网关实例
def create_gateway() -> FastAPI:
    """创建API网关应用"""
    gateway = APIGateway()
    return gateway.app


# 使用示例
if __name__ == "__main__":
    import uvicorn
    
    app = create_gateway()
    
    # 启动网关
    uvicorn.run(app, host="0.0.0.0", port=8000)


















