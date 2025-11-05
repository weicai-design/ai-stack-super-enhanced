"""
Semantic Grouping API
语义分组API

根据需求1.6：语义分组功能
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

import sys
from pathlib import Path

# 添加路径
erp_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(erp_dir))

from core.semantic_grouping import SemanticGrouper
from api.app import _docs, _load_model, require_api_key

router = APIRouter(prefix="/rag", tags=["Semantic Grouping API"])


class GroupingRequest(BaseModel):
    """分组请求模型"""
    k: Optional[int] = 8  # 分组数量
    min_items: Optional[int] = 2  # 最小分组大小
    method: Optional[str] = "kmeans"  # 分组方法：kmeans, hierarchical


class GroupingResponse(BaseModel):
    """分组响应模型"""
    k: int
    groups: List[Dict[str, Any]]
    total_items: int
    grouped_items: int


@router.get("/groups", response_model=Dict[str, Any])
async def get_semantic_groups(
    k: int = Query(8, ge=2, le=50, description="分组数量"),
    min_items: int = Query(2, ge=1, description="最小分组大小"),
    method: str = Query("kmeans", description="分组方法：kmeans, hierarchical"),
) -> Dict[str, Any]:
    """
    获取语义分组结果（需求1.6）
    
    功能：
    - 对RAG库中的文档进行语义分组
    - 支持K-means和层次聚类
    - 返回分组结果和统计信息
    
    Args:
        k: 分组数量（2-50）
        min_items: 最小分组大小
        method: 分组方法
        
    Returns:
        分组结果
    """
    try:
        # 延迟导入避免循环依赖
        _docs = _get_docs()
        load_model_func = _get_model_func()
        
        if not _docs:
            return {
                "success": True,
                "k": k,
                "groups": [],
                "total_items": 0,
                "grouped_items": 0,
                "message": "RAG库为空",
            }

        # 获取嵌入模型
        model = load_model_func()
        
        # 创建分组器
        def embed_fn(text: str):
            return model.encode(text, convert_to_numpy=True)

        grouper = SemanticGrouper(embed_fn=embed_fn)

        # 提取所有文档文本
        texts = [doc.text for doc in _docs]

        # 执行分组
        if method == "hierarchical":
            # 使用层次聚类（需要sklearn）
            try:
                from sklearn.cluster import AgglomerativeClustering
                import numpy as np
                
                embeddings = np.array([embed_fn(t) for t in texts])
                if len(embeddings) < k:
                    k = len(embeddings)
                
                clustering = AgglomerativeClustering(
                    n_clusters=k,
                    metric="cosine",
                    linkage="average",
                )
                labels = clustering.fit_predict(embeddings)
                
                # 构建分组
                groups_dict = {}
                for idx, label in enumerate(labels):
                    if label not in groups_dict:
                        groups_dict[label] = []
                    groups_dict[label].append(idx)
                
                groups = []
                for group_id, indices in groups_dict.items():
                    if len(indices) >= min_items:
                        group_items = [
                            {
                                "doc_id": _docs[i].id,
                                "text": _docs[i].text[:200],  # 只返回前200字符
                                "path": _docs[i].path,
                            }
                            for i in indices
                        ]
                        groups.append({
                            "id": int(group_id),
                            "items": group_items,
                            "count": len(group_items),
                        })
                
                return {
                    "success": True,
                    "k": len(groups),
                    "method": method,
                    "groups": groups,
                    "total_items": len(texts),
                    "grouped_items": sum(len(g["items"]) for g in groups),
                }
            except ImportError:
                # 如果没有sklearn，回退到K-means
                method = "kmeans"

        # 使用K-means（默认）
        result = grouper.cluster(texts, k=k)

        # 构建响应
        groups = []
        for group in result.get("groups", []):
            items = group.get("items", [])
            if len(items) >= min_items:
                group_items = [
                    {
                        "doc_id": _docs[i].id,
                        "text": _docs[i].text[:200],  # 只返回前200字符
                        "path": _docs[i].path,
                    }
                    for i in items
                ]
                groups.append({
                    "id": group.get("id"),
                    "items": group_items,
                    "count": len(group_items),
                })

        return {
            "success": True,
            "k": result.get("k", k),
            "method": method,
            "groups": groups,
            "total_items": len(texts),
            "grouped_items": sum(len(g["items"]) for g in groups),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"语义分组失败: {str(e)}"
        )


@router.post("/groups", response_model=Dict[str, Any])
async def create_semantic_groups(
    request: GroupingRequest,
) -> Dict[str, Any]:
    """
    创建语义分组（POST方式）
    
    Args:
        request: 分组请求
        _: API密钥验证
        
    Returns:
        分组结果
    """
    return await get_semantic_groups(
        k=request.k or 8,
        min_items=request.min_items or 2,
        method=request.method or "kmeans",
    )

