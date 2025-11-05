"""
AI Stack API Gateway
统一API网关，连接所有AI Stack服务
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import time
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_gateway")

app = FastAPI(
    title="AI Stack API Gateway",
    description="统一API网关，连接所有AI Stack服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # OpenWebUI
        "http://localhost:8012",  # ERP Frontend
        "http://localhost:*",     # 所有本地服务
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务配置
SERVICES = {
    "rag": "http://localhost:8011",
    "erp": "http://localhost:8013",
    "stock": "http://localhost:8014",
    "trend": "http://localhost:8015",
    "content": "http://localhost:8016",
    "task": "http://localhost:8017",
    "resource": "http://localhost:8018",
    "learning": "http://localhost:8019",
}

# 请求计数和监控
request_count = 0
error_count = 0


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    global request_count
    request_count += 1
    
    start_time = time.time()
    
    logger.info(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    logger.info(f"Status: {response.status_code}, Time: {process_time:.2f}ms")
    
    return response


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AI Stack API Gateway",
        "version": "1.0.0",
        "services": list(SERVICES.keys()),
        "status": "running",
        "requests_served": request_count,
        "errors": error_count
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/gateway/services")
async def list_services():
    """列出所有服务"""
    return {
        "services": SERVICES,
        "count": len(SERVICES)
    }


@app.get("/gateway/status")
async def check_all_services():
    """检查所有服务状态"""
    results = {}
    
    async with httpx.AsyncClient() as client:
        for name, url in SERVICES.items():
            try:
                response = await client.get(f"{url}/health", timeout=3.0)
                results[name] = {
                    "status": "running" if response.status_code == 200 else "error",
                    "url": url,
                    "response_code": response.status_code
                }
            except Exception as e:
                results[name] = {
                    "status": "stopped",
                    "url": url,
                    "error": str(e)
                }
    
    running_count = sum(1 for r in results.values() if r["status"] == "running")
    
    return {
        "services": results,
        "summary": {
            "total": len(SERVICES),
            "running": running_count,
            "stopped": len(SERVICES) - running_count,
            "availability": f"{(running_count/len(SERVICES)*100):.1f}%"
        }
    }


# ===== RAG系统路由 =====

@app.get("/gateway/rag/search")
async def rag_search(query: str, top_k: int = 5):
    """RAG知识搜索"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['rag']}/rag/search",
                params={"query": query, "top_k": top_k},
                timeout=15.0
            )
            return response.json()
    except Exception as e:
        global error_count
        error_count += 1
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gateway/rag/ingest")
async def rag_ingest(data: dict):
    """RAG文档摄入"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICES['rag']}/rag/ingest",
                json=data,
                timeout=60.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gateway/kg/snapshot")
async def kg_snapshot():
    """知识图谱快照"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['rag']}/kg/snapshot",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gateway/kg/query")
async def kg_query(query: str, query_type: str = "entity"):
    """知识图谱查询"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['rag']}/kg/query",
                params={"query": query, "query_type": query_type},
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== ERP系统路由 =====

@app.get("/gateway/erp/financial")
async def erp_financial(period: str = "month"):
    """ERP财务数据"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['erp']}/api/finance/dashboard",
                params={"period": period},
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gateway/erp/orders")
async def erp_orders(status: Optional[str] = None, limit: int = 50):
    """ERP订单查询"""
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['erp']}/api/business/orders",
                params=params,
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gateway/erp/customers")
async def erp_customers(limit: int = 50):
    """ERP客户查询"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['erp']}/api/business/customers",
                params={"limit": limit},
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gateway/erp/production")
async def erp_production():
    """ERP生产状态"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['erp']}/api/production/plans",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 股票系统路由 =====

@app.get("/gateway/stock/price/{code}")
async def stock_price(code: str):
    """股票价格"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['stock']}/api/stock/price/{code}",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gateway/stock/analyze/{code}")
async def stock_analyze(code: str):
    """股票策略分析"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['stock']}/api/stock/analyze/{code}",
                timeout=15.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gateway/stock/sentiment")
async def stock_sentiment():
    """市场情绪"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['stock']}/api/stock/sentiment",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 内容创作路由 =====

@app.post("/gateway/content/generate")
async def content_generate(data: dict):
    """生成内容"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICES['content']}/api/content/generate",
                json=data,
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 任务代理路由 =====

@app.get("/gateway/task/list")
async def task_list():
    """任务列表"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['task']}/api/tasks",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 资源管理路由 =====

@app.get("/gateway/resource/stats")
async def resource_stats():
    """资源统计"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICES['resource']}/api/resources/stats",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 监控和统计 =====

@app.get("/gateway/stats")
async def gateway_stats():
    """网关统计"""
    return {
        "requests_total": request_count,
        "errors_total": error_count,
        "services_count": len(SERVICES),
        "uptime": "运行中"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)



