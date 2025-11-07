"""
RAG API - FastAPI主程序
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.file_processor import FileProcessor
from processors.text_processor import TextProcessor
from processors.preprocessor import Preprocessor
from storage.chroma_store import ChromaStore
from core.retriever import Retriever

# 创建FastAPI应用
app = FastAPI(
    title="RAG & Knowledge Graph API",
    description="智能知识管理系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
file_processor = FileProcessor()
text_processor = TextProcessor()
preprocessor = Preprocessor()
vector_store = ChromaStore()
retriever = Retriever(vector_store=vector_store)


# ========== Pydantic模型 ==========

class QueryRequest(BaseModel):
    """查询请求"""
    query: str
    top_k: Optional[int] = 5
    mode: Optional[str] = "hybrid"  # vector, keyword, hybrid
    filters: Optional[Dict] = None


class DocumentRequest(BaseModel):
    """添加文档请求"""
    content: str
    metadata: Optional[Dict] = None
    source: str = "manual"


# ========== 根端点 ==========

@app.get("/")
def root():
    """API根路径"""
    return {
        "message": "RAG & Knowledge Graph API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "upload": "/api/upload",
            "query": "/api/query",
            "documents": "/api/documents",
            "statistics": "/api/statistics"
        }
    }


@app.get("/health")
def health_check():
    """健康检查"""
    stats = vector_store.get_statistics()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "file_processor": "ok",
            "text_processor": "ok",
            "preprocessor": "ok",
            "vector_store": "ok" if stats.get("total_documents", 0) >= 0 else "error",
            "retriever": "ok"
        },
        "statistics": stats
    }


# ========== 文件上传端点 ==========

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    auto_process: bool = Query(True, description="是否自动处理文件")
):
    """
    上传文件到RAG系统
    
    - 支持多种文件格式
    - 自动提取内容
    - 可选择是否立即处理
    """
    try:
        # 保存上传的文件
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        result = {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path),
            "uploaded_at": datetime.now().isoformat()
        }
        
        # 如果启用自动处理
        if auto_process:
            # 处理文件
            process_result = file_processor.process_file(str(file_path))
            
            if process_result.get("success"):
                # 预处理
                preprocess_result = preprocessor.preprocess(
                    process_result["content"],
                    metadata=process_result["metadata"]
                )
                
                # 分块
                chunks = text_processor.split_text(
                    preprocess_result["processed_text"]
                )
                
                result["processed"] = True
                result["chunks_count"] = len(chunks)
                result["content_length"] = len(process_result["content"])
            else:
                result["processed"] = False
                result["error"] = process_result.get("error")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 文档管理端点 ==========

@app.post("/api/documents")
def add_document(request: DocumentRequest):
    """
    添加文档到RAG系统
    
    - 接收纯文本或结构化数据
    - 自动预处理
    - 存储到向量库
    """
    try:
        # 预处理
        preprocess_result = preprocessor.preprocess(
            request.content,
            metadata=request.metadata
        )
        
        if not preprocess_result["passed_validation"]:
            return {
                "success": False,
                "error": "文档验证未通过",
                "warnings": preprocess_result["warnings"]
            }
        
        # 分块
        chunks = text_processor.split_text(
            preprocess_result["processed_text"]
        )
        
        # TODO: 向量化并存储
        # 目前由于没有嵌入模型，暂时跳过
        
        return {
            "success": True,
            "source": request.source,
            "original_length": len(request.content),
            "processed_length": preprocess_result["final_length"],
            "chunks_count": len(chunks),
            "warnings": preprocess_result["warnings"],
            "added_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 查询端点 ==========

@app.post("/api/query")
def query_knowledge(request: QueryRequest):
    """
    查询知识库
    
    - 支持多种检索模式
    - 元数据过滤
    - 返回相关文档
    """
    try:
        # TODO: 生成查询向量
        # 目前使用None，检索器会处理
        
        result = retriever.retrieve(
            query=request.query,
            query_embedding=None,  # TODO: 实际应用需要生成向量
            top_k=request.top_k,
            mode=request.mode,
            filters=request.filters
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/simple")
def simple_query(
    q: str = Query(..., description="查询文本"),
    top_k: int = Query(5, description="返回结果数量")
):
    """
    简单查询接口（GET方法）
    
    - 快速查询
    - 默认使用混合检索
    """
    try:
        result = retriever.retrieve(
            query=q,
            query_embedding=None,
            top_k=top_k,
            mode="hybrid"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 统计端点 ==========

@app.get("/api/statistics")
def get_statistics():
    """
    获取系统统计信息
    
    - 文档数量
    - 存储大小
    - 其他指标
    """
    try:
        stats = vector_store.get_statistics()
        
        # 添加更多统计信息
        stats["api_version"] = "1.0.0"
        stats["timestamp"] = datetime.now().isoformat()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 管理端点 ==========

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    """删除文档"""
    try:
        result = vector_store.delete([doc_id])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
def reset_system(confirm: bool = Query(False, description="确认重置")):
    """
    重置系统（危险操作）
    
    - 删除所有数据
    - 需要确认
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="需要确认重置操作（设置 confirm=true）"
        )
    
    try:
        result = vector_store.reset()
        preprocessor.reset_dedup_cache()
        
        return {
            "success": True,
            "message": "系统已重置",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 辅助端点 ==========

@app.get("/api/formats")
def get_supported_formats():
    """获取支持的文件格式"""
    return file_processor.get_supported_formats_info()


@app.get("/api/config")
def get_config():
    """获取系统配置信息"""
    return {
        "file_processor": file_processor.config,
        "text_processor": text_processor.config,
        "preprocessor": preprocessor.config,
        "vector_store": vector_store.config,
        "retriever": retriever.config
    }


# 运行服务器
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("  🚀 启动RAG API服务器")
    print("="*70)
    print(f"\n  访问地址: http://localhost:8014")
    print(f"  API文档: http://localhost:8014/docs")
    print(f"  健康检查: http://localhost:8014/health")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8014,
        reload=True,
        log_level="info"
    )



