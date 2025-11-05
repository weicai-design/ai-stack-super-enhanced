#!/usr/bin/env python3
"""
为未注册的API模块创建降级router
这样即使导入失败，端点也能注册
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

def create_fallback_router(prefix: str, tag: str, endpoint: str, error_msg: str = "功能暂未完全实现"):
    """创建降级router"""
    router = APIRouter(prefix=prefix, tags=[tag])
    
    if endpoint == "query":
        @router.post("/query")
        async def fallback_query():
            raise HTTPException(status_code=503, detail=error_msg)
    elif endpoint == "retrieve":
        @router.post("/retrieve")
        async def fallback_retrieve():
            raise HTTPException(status_code=503, detail=error_msg)
    elif endpoint == "execute":
        @router.post("/execute")
        async def fallback_execute():
            raise HTTPException(status_code=503, detail=error_msg)
    elif endpoint == "batch_query":
        @router.post("/query")
        async def fallback_batch_query():
            raise HTTPException(status_code=503, detail=error_msg)
    elif endpoint == "stats":
        @router.get("/stats")
        async def fallback_stats():
            raise HTTPException(status_code=503, detail=error_msg)
    
    return router

# 定义需要创建的降级router
FALLBACK_ROUTERS = [
    ("/expert", "Expert RAG API", "query", "专家系统功能暂未完全实现"),
    ("/self-rag", "Self-RAG API", "retrieve", "Self-RAG功能暂未完全实现"),
    ("/agentic-rag", "Agentic RAG API", "execute", "Agentic RAG功能暂未完全实现"),
    ("/kg/batch", "Knowledge Graph Batch API", "batch_query", "知识图谱批量功能暂未完全实现"),
    ("/graph-db", "Graph Database API", "stats", "图数据库功能暂未完全实现"),
]

