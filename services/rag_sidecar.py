#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：RAG Hub Sidecar 微服务

可使用 `uvicorn services.rag_sidecar:app --port 8011` 启动。
"""

from fastapi import FastAPI, Body
from pydantic import BaseModel, Field

from 🚀 Super Agent Main Interface.core.dual_rag_engine import DualRAGEngine
from 🚀 Super Agent Main Interface.core.rag_service_adapter import RAGServiceAdapter

app = FastAPI(title="RAG Hub Service", version="v1")
rag_adapter = RAGServiceAdapter()
rag_engine = DualRAGEngine(rag_service=rag_adapter)


class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    top_k: int = Field(5, ge=1, le=10)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/rag/search")
async def rag_search(req: SearchRequest):
    result = await rag_engine.first_rag_retrieval(user_input=req.query, top_k=req.top_k)
    return result.to_dict()


@app.post("/v1/rag/experience")
async def rag_experience(
    query: str = Body(...),
    execution_result: dict = Body(default_factory=dict),
):
    rag1 = await rag_engine.first_rag_retrieval(user_input=query)
    rag2 = await rag_engine.second_rag_retrieval(
        user_input=query,
        execution_result={"module": execution_result.get("module", "rag"), "result": execution_result},
        rag1_result=rag1,
    )
    return {"rag1": rag1.to_dict(), "rag2": rag2.to_dict()}

