"""
数据导出API
提供Excel、CSV、PDF等格式的数据导出功能
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import io

from core.data_exporter import DataExporter

router = APIRouter(prefix="/api/export", tags=["Export API"])

# 初始化导出器
exporter = DataExporter()


class ExportRequest(BaseModel):
    """导出请求模型"""
    data: List[Dict[str, Any]]
    format: str = "excel"  # excel, csv, pdf
    filename: Optional[str] = None
    title: Optional[str] = None
    template_type: Optional[str] = None  # standard, financial, production


@router.post("/excel")
async def export_to_excel(request: ExportRequest):
    """
    导出数据到Excel
    
    Args:
        request: 导出请求
        
    Returns:
        Excel文件流
    """
    try:
        filename = request.filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        if request.template_type:
            file_bytes = await exporter.export_with_template(
                request.data,
                template_type=request.template_type
            )
        else:
            file_bytes = await exporter.export_to_excel(
                request.data,
                filename=filename,
                title=request.title
            )
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/csv")
async def export_to_csv(request: ExportRequest):
    """
    导出数据到CSV
    
    Args:
        request: 导出请求
        
    Returns:
        CSV文件流
    """
    try:
        filename = request.filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_bytes = await exporter.export_to_csv(request.data, filename=filename)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/pdf")
async def export_to_pdf(request: ExportRequest):
    """
    导出数据到PDF（HTML格式，可打印为PDF）
    
    Args:
        request: 导出请求
        
    Returns:
        HTML文件流（浏览器可打印为PDF）
    """
    try:
        filename = request.filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        title = request.title or "数据报表"
        file_bytes = await exporter.export_to_pdf(request.data, title=title, filename=filename)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/multiple-sheets")
async def export_multiple_sheets(
    sheets_data: Dict[str, List[Dict[str, Any]]],
    filename: Optional[str] = None
):
    """
    导出多工作表Excel
    
    Args:
        sheets_data: 工作表数据字典 {sheet_name: [data]}
        filename: 文件名（可选）
        
    Returns:
        Excel文件流
    """
    try:
        filename = filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_bytes = await exporter.export_multiple_sheets(sheets_data, filename=filename)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/excel-with-charts")
async def export_excel_with_charts(
    request: ExportRequest,
    chart_config: Optional[Dict[str, Any]] = None
):
    """
    导出带图表的Excel
    
    Args:
        request: 导出请求
        chart_config: 图表配置
        
    Returns:
        Excel文件流
    """
    try:
        filename = request.filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_bytes = await exporter.export_with_charts(request.data, chart_config)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/batch")
async def batch_export(
    export_tasks: List[Dict[str, Any]] = Body(...),
    filename: Optional[str] = None
):
    """
    批量导出（多个数据源导出到一个Excel文件）
    
    Args:
        export_tasks: 导出任务列表 [{data, sheet_name, title}]
        filename: 文件名（可选）
        
    Returns:
        Excel文件流
    """
    try:
        filename = filename or f"batch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_bytes = await exporter.export_batch(export_tasks)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量导出失败: {str(e)}")


@router.post("/schedule")
async def schedule_export(export_config: Dict[str, Any]):
    """
    定时导出配置
    
    Args:
        export_config: 导出配置
        
    Returns:
        调度结果
    """
    try:
        result = await exporter.schedule_export(export_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置失败: {str(e)}")
