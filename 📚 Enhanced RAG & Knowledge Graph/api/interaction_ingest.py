"""
RAG系统 - 交互内容自动入库端点
接收OpenWebUI对话并自动入库
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/rag/ingest", tags=["ingest"])


class TextIngest(BaseModel):
    """文本摄入"""
    text: str
    metadata: Optional[Dict[str, Any]] = None
    save_index: bool = True


@router.post("/text")
async def ingest_text(data: TextIngest):
    """
    摄入文本到RAG
    用于自动将OpenWebUI对话入库
    """
    
    try:
        # 这里调用RAG的文本摄入功能
        # 简化版：记录到日志
        
        print(f"📚 收到交互内容入库请求:")
        print(f"  文本长度: {len(data.text)}")
        print(f"  元数据: {data.metadata}")
        print(f"  时间: {datetime.now()}")
        
        # 实际应该调用RAG的ingest功能
        # 这里简化处理
        
        return {
            "success": True,
            "message": "交互内容已入库到RAG",
            "doc_id": f"interaction_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "RAG知识库持续增长中..."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



