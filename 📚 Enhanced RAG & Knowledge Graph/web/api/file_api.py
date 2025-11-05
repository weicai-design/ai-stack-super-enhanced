#!/usr/bin/env python3
"""
Enhanced File Processing API
对应需求: 1.1 所有格式文件处理, 1.2 四项预处理, 1.3 去伪处理
文件位置: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/api/115. file-api.py
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiofiles
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pipelines.multi_stage_preprocessor import MultiStagePreprocessor
from pipelines.truth_verification_pipeline import TruthVerificationPipeline

# 导入文件处理模块
from processors.file_processors.universal_file_parser import UniversalFileParser
from pydantic import BaseModel, Field

logger = logging.getLogger("file_api")

# 创建路由
router = APIRouter(
    prefix="/files",
    tags=["File Processing API"],
    responses={404: {"description": "Not found"}},
)


# Pydantic模型定义
class FileUploadResponse(BaseModel):
    """文件上传响应模型"""

    success: bool
    file_id: str
    filename: str
    file_size: int
    file_type: str
    message: str


class FileProcessRequest(BaseModel):
    """文件处理请求模型"""

    file_ids: List[str] = Field(..., description="文件ID列表")
    preprocess: bool = Field(True, description="是否预处理")
    verify_truth: bool = Field(True, description="是否验证真实性")
    extract_entities: bool = Field(True, description="是否提取实体")
    chunk_documents: bool = Field(True, description="是否分块文档")


class FileProcessResponse(BaseModel):
    """文件处理响应模型"""

    success: bool
    processed_files: List[Dict[str, Any]]
    failed_files: List[Dict[str, Any]]
    process_id: str


class FileInfo(BaseModel):
    """文件信息模型"""

    file_id: str
    filename: str
    file_size: int
    file_type: str
    upload_time: str
    status: str
    metadata: Dict[str, Any]


class BatchProcessRequest(BaseModel):
    """批处理请求模型"""

    operation: str = Field(..., description="操作类型")
    file_ids: List[str] = Field(..., description="文件ID列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="处理参数")


# 全局组件实例
_file_parser = None
_preprocessor = None
_truth_verifier = None


# 依赖注入
async def get_file_parser() -> UniversalFileParser:
    """获取文件解析器实例"""
    global _file_parser
    if _file_parser is None:
        try:
            _file_parser = UniversalFileParser()
            await _file_parser.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize file parser: {str(e)}")
            raise HTTPException(status_code=503, detail="File parser not initialized")
    return _file_parser


async def get_preprocessor() -> MultiStagePreprocessor:
    """获取预处理器实例"""
    file_parser = await get_file_parser()
    return file_parser.preprocessor


async def get_truth_verifier() -> TruthVerificationPipeline:
    """获取真实性验证器实例"""
    global _truth_verifier
    if _truth_verifier is None:
        try:
            _truth_verifier = TruthVerificationPipeline()
            await _truth_verifier.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize truth verifier: {str(e)}")
            raise HTTPException(
                status_code=503, detail="Truth verifier not initialized"
            )
    return _truth_verifier


# 文件存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# API路由
@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="上传的文件"),
    preprocess: bool = Form(True, description="是否预处理"),
    file_parser: UniversalFileParser = Depends(get_file_parser),
):
    """
    上传文件

    Args:
        background_tasks: 后台任务
        file: 上传的文件
        preprocess: 是否预处理
        file_parser: 文件解析器

    Returns:
        FileUploadResponse: 上传响应
    """
    try:
        # 生成文件ID
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, saved_filename)

        # 保存文件
        file_size = 0
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
            file_size = len(content)

        # 获取文件类型
        file_type = file.content_type or "unknown"

        # 在后台处理文件
        if preprocess:
            background_tasks.add_task(
                process_uploaded_file, file_path, file_id, file.filename, file_parser
            )

        logger.info(
            f"File uploaded: {file.filename} -> {file_id}, size: {file_size} bytes"
        )

        return FileUploadResponse(
            success=True,
            file_id=file_id,
            filename=file.filename,
            file_size=file_size,
            file_type=file_type,
            message="File uploaded successfully",
        )

    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


async def process_uploaded_file(
    file_path: str,
    file_id: str,
    original_filename: str,
    file_parser: UniversalFileParser,
):
    """处理上传的文件（后台任务）"""
    try:
        # 解析文件
        parsed_data = await file_parser.parse_file(file_path)

        # 存储解析结果
        result_path = os.path.join(UPLOAD_DIR, f"{file_id}_parsed.json")
        async with aiofiles.open(result_path, "w", encoding="utf-8") as f:
            await f.write(
                json.dumps(
                    {
                        "file_id": file_id,
                        "original_filename": original_filename,
                        "parsed_data": parsed_data,
                        "processed_at": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )

        logger.info(f"File processed successfully: {file_id}")

    except Exception as e:
        logger.error(f"File processing failed: {file_id}, error: {str(e)}")


@router.post("/process", response_model=FileProcessResponse)
async def process_files(
    request: FileProcessRequest,
    background_tasks: BackgroundTasks,
    file_parser: UniversalFileParser = Depends(get_file_parser),
    preprocessor: MultiStagePreprocessor = Depends(get_preprocessor),
    truth_verifier: TruthVerificationPipeline = Depends(get_truth_verifier),
):
    """
    处理文件

    Args:
        request: 处理请求
        background_tasks: 后台任务
        file_parser: 文件解析器
        preprocessor: 预处理器
        truth_verifier: 真实性验证器

    Returns:
        FileProcessResponse: 处理响应
    """
    try:
        process_id = str(uuid.uuid4())

        # 在后台执行文件处理
        background_tasks.add_task(
            batch_process_files,
            request.file_ids,
            request.preprocess,
            request.verify_truth,
            request.extract_entities,
            request.chunk_documents,
            file_parser,
            preprocessor,
            truth_verifier,
            process_id,
        )

        logger.info(
            f"File processing started: process_id={process_id}, file_count={len(request.file_ids)}"
        )

        return FileProcessResponse(
            success=True, processed_files=[], failed_files=[], process_id=process_id
        )

    except Exception as e:
        logger.error(f"File processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


async def batch_process_files(
    file_ids: List[str],
    preprocess: bool,
    verify_truth: bool,
    extract_entities: bool,
    chunk_documents: bool,
    file_parser: UniversalFileParser,
    preprocessor: MultiStagePreprocessor,
    truth_verifier: TruthVerificationPipeline,
    process_id: str,
):
    """批量处理文件（后台任务）"""
    processed_files = []
    failed_files = []

    for file_id in file_ids:
        try:
            file_info = await _get_file_info(file_id)
            if not file_info:
                failed_files.append({"file_id": file_id, "error": "File not found"})
                continue

            file_path = os.path.join(
                UPLOAD_DIR, f"{file_id}{os.path.splitext(file_info['filename'])[1]}"
            )

            # 解析文件
            parsed_data = await file_parser.parse_file(file_path)

            # 预处理
            if preprocess:
                parsed_data = await preprocessor.process(parsed_data)

            # 验证真实性
            if verify_truth:
                truth_result = await truth_verifier.verify_content(
                    parsed_data.get("content", "")
                )
                parsed_data["truth_verification"] = truth_result

            # 提取实体
            if extract_entities:
                entities = await file_parser.extract_entities(
                    parsed_data.get("content", "")
                )
                parsed_data["entities"] = entities

            # 分块文档
            if chunk_documents:
                chunks = await file_parser.chunk_document(parsed_data)
                parsed_data["chunks"] = chunks

            # 保存处理结果
            result_path = os.path.join(UPLOAD_DIR, f"{file_id}_processed.json")
            async with aiofiles.open(result_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(parsed_data, ensure_ascii=False, indent=2))

            processed_files.append(
                {
                    "file_id": file_id,
                    "filename": file_info["filename"],
                    "status": "processed",
                    "processed_at": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            failed_files.append({"file_id": file_id, "error": str(e)})
            logger.warning(f"Failed to process file {file_id}: {str(e)}")

    logger.info(
        f"Batch file processing completed: process_id={process_id}, "
        f"processed={len(processed_files)}, failed={len(failed_files)}"
    )


@router.get("/info/{file_id}")
async def get_file_info(
    file_id: str, file_parser: UniversalFileParser = Depends(get_file_parser)
):
    """
    获取文件信息

    Args:
        file_id: 文件ID
        file_parser: 文件解析器

    Returns:
        FileInfo: 文件信息
    """
    try:
        file_info = await _get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")

        return FileInfo(**file_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file info: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"File info retrieval failed: {str(e)}"
        )


async def _get_file_info(file_id: str) -> Optional[Dict[str, Any]]:
    """获取文件信息（内部函数）"""
    try:
        # 查找文件
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_id) and not filename.endswith(
                ("_parsed.json", "_processed.json")
            ):
                file_path = os.path.join(UPLOAD_DIR, filename)
                stat = os.stat(file_path)

                return {
                    "file_id": file_id,
                    "filename": filename,
                    "file_size": stat.st_size,
                    "file_type": "unknown",  # 可以添加MIME类型检测
                    "upload_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "status": "uploaded",
                    "metadata": {},
                }

        return None

    except Exception:
        return None


@router.get("/list")
async def list_files(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页大小"),
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
):
    """
    列出文件

    Args:
        page: 页码
        page_size: 每页大小
        file_type: 文件类型过滤

    Returns:
        Dict: 文件列表
    """
    try:
        files = []
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        for filename in os.listdir(UPLOAD_DIR):
            if not filename.endswith(("_parsed.json", "_processed.json")):
                file_id = filename.split(".")[0]
                file_info = await _get_file_info(file_id)
                if file_info:
                    if file_type and file_info["file_type"] != file_type:
                        continue
                    files.append(file_info)

        # 分页
        paginated_files = files[start_idx:end_idx]

        return {
            "success": True,
            "files": paginated_files,
            "total_count": len(files),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(files) + page_size - 1) // page_size,
        }

    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File listing failed: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(
    file_id: str, file_parser: UniversalFileParser = Depends(get_file_parser)
):
    """
    删除文件

    Args:
        file_id: 文件ID
        file_parser: 文件解析器

    Returns:
        Dict: 删除结果
    """
    try:
        deleted_count = 0

        # 删除所有相关文件
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                os.remove(file_path)
                deleted_count += 1

        if deleted_count > 0:
            logger.info(f"File deleted: {file_id}, deleted_files: {deleted_count}")
            return {
                "success": True,
                "message": f"File {file_id} deleted successfully",
                "deleted_files": deleted_count,
            }
        else:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(
    file_id: str, file_parser: UniversalFileParser = Depends(get_file_parser)
):
    """
    下载文件

    Args:
        file_id: 文件ID
        file_parser: 文件解析器

    Returns:
        StreamingResponse: 文件流
    """
    try:
        file_info = await _get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")

        filename = file_info["filename"]
        file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")

        return StreamingResponse(
            open(file_path, "rb"),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")


@router.get("/processed/{file_id}")
async def get_processed_result(
    file_id: str, file_parser: UniversalFileParser = Depends(get_file_parser)
):
    """
    获取文件处理结果

    Args:
        file_id: 文件ID
        file_parser: 文件解析器

    Returns:
        Dict: 处理结果
    """
    try:
        result_path = os.path.join(UPLOAD_DIR, f"{file_id}_processed.json")
        if not os.path.exists(result_path):
            raise HTTPException(
                status_code=404, detail=f"Processed result for {file_id} not found"
            )

        async with aiofiles.open(result_path, "r", encoding="utf-8") as f:
            content = await f.read()
            result = json.loads(content)

        return {
            "success": True,
            "file_id": file_id,
            "processed_result": result,
            "retrieved_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processed result: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Processed result retrieval failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        file_parser = await get_file_parser()
        preprocessor = await get_preprocessor()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "file_parser": file_parser is not None,
                "preprocessor": preprocessor is not None,
                "truth_verifier": _truth_verifier is not None,
            },
        }
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
