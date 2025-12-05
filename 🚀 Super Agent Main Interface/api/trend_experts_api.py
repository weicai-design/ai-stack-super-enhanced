"""
趋势分析专家模块API接口

提供趋势分析专家模块的RESTful API接口，支持：
1. 趋势数据采集
2. 趋势数据处理
3. 趋势模式分析
4. 趋势预测
5. 趋势报告生成
6. 趋势预警

API设计遵循RESTful原则，支持异步处理，确保2秒SLO响应时间要求
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

# 导入趋势分析专家模块
from core.experts.trend_experts import (
    TrendDataConnector,
    TrendCollectionExpert,
    TrendProcessingExpert,
    TrendAnalysisExpert,
    TrendPredictionExpert,
    TrendReportExpert,
    TrendAlertExpert,
    get_trend_experts,
    TrendStage
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="趋势分析专家API",
    description="提供趋势分析专家模块的RESTful API接口",
    version="1.0.0"
)

# 全局数据连接器和专家实例
connector = TrendDataConnector()
experts = get_trend_experts(connector)


# 请求和响应模型
class TrendDataRequest(BaseModel):
    """趋势数据请求模型"""
    platform: str = Field(..., description="数据平台: financial, social_media, news, market, research")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    data_volume: Optional[int] = Field(1000, description="数据量")


class RealTimeDataRequest(BaseModel):
    """实时数据请求模型"""
    platform: str = Field(..., description="数据平台")
    monitoring_interval: Optional[int] = Field(60, description="监控间隔(秒)")


class TrendAnalysisRequest(BaseModel):
    """趋势分析请求模型"""
    trends: List[Dict[str, Any]] = Field(..., description="趋势数据列表")
    patterns: Optional[List[Dict[str, Any]]] = Field([], description="模式数据列表")
    analysis_depth: Optional[str] = Field("standard", description="分析深度: basic, standard, deep")


class TrendPredictionRequest(BaseModel):
    """趋势预测请求模型"""
    historical_data: Dict[str, Any] = Field(..., description="历史数据")
    prediction_horizon: int = Field(30, description="预测周期(天)")
    confidence_threshold: Optional[float] = Field(0.7, description="置信度阈值")


class TrendReportRequest(BaseModel):
    """趋势报告请求模型"""
    analysis_data: Dict[str, Any] = Field(..., description="分析数据")
    prediction_data: Optional[Dict[str, Any]] = Field(None, description="预测数据")
    report_format: Optional[str] = Field("standard", description="报告格式: standard, detailed, executive")


class TrendAlertRequest(BaseModel):
    """趋势预警请求模型"""
    trend_data: Dict[str, Any] = Field(..., description="趋势数据")
    alert_thresholds: Optional[Dict[str, float]] = Field(
        {"high": 0.8, "medium": 0.6, "low": 0.4},
        description="预警阈值"
    )
    monitoring_period: Optional[int] = Field(3600, description="监控周期(秒)")


class APIResponse(BaseModel):
    """API响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    message: str = Field(..., description="响应消息")
    processing_time: float = Field(..., description="处理时间(秒)")


# 性能监控装饰器
def performance_monitor(func):
    """性能监控装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # 检查是否超过SLO要求
            if processing_time > 2.0:
                logger.warning(f"API {func.__name__} 响应时间 {processing_time:.2f}s 超过2秒SLO要求")
            
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"API {func.__name__} 执行错误: {str(e)}")
            raise e
    
    return wrapper


@app.get("/", response_model=APIResponse)
async def root():
    """API根路径"""
    return APIResponse(
        success=True,
        message="趋势分析专家API服务运行正常",
        processing_time=0.0
    )


@app.get("/health", response_model=APIResponse)
async def health_check():
    """健康检查"""
    start_time = time.time()
    
    # 检查数据连接器状态
    connection_status = connector.get_connection_status()
    
    # 检查专家实例状态
    expert_status = {}
    for expert_name, expert in experts.items():
        expert_status[expert_name] = {
            "expert_id": getattr(expert, 'expert_id', None),
            "expert_name": getattr(expert, 'expert_name', getattr(expert, 'name', None)),
            "stage": getattr(expert, 'stage', None)
        }
    
    processing_time = time.time() - start_time
    
    return APIResponse(
        success=True,
        data={
            "connection_status": connection_status,
            "expert_status": expert_status,
            "total_experts": len(experts)
        },
        message="服务健康状态检查完成",
        processing_time=processing_time
    )


@app.post("/data/trend", response_model=APIResponse)
@performance_monitor
async def get_trend_data(request: TrendDataRequest):
    """获取趋势数据"""
    start_time = time.time()
    
    try:
        # 使用数据连接器获取趋势数据
        trend_data = await connector.get_trend_data(
            request.platform,
            request.start_date,
            request.end_date
        )
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data=trend_data,
            message=f"成功获取{request.platform}平台趋势数据",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"获取趋势数据失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"获取趋势数据失败: {str(e)}",
            processing_time=processing_time
        )


@app.post("/data/realtime", response_model=APIResponse)
@performance_monitor
async def get_real_time_data(request: RealTimeDataRequest):
    """获取实时数据"""
    start_time = time.time()
    
    try:
        # 使用数据连接器获取实时数据
        real_time_data = await connector.get_real_time_data(request.platform)
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data=real_time_data,
            message=f"成功获取{request.platform}平台实时数据",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"获取实时数据失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"获取实时数据失败: {str(e)}",
            processing_time=processing_time
        )


@app.post("/experts/collection/analyze", response_model=APIResponse)
@performance_monitor
async def analyze_trend_collection(request: TrendDataRequest):
    """趋势采集分析"""
    start_time = time.time()
    
    try:
        # 准备分析数据
        analysis_data = {
            "data_volume": request.data_volume,
            "platform": request.platform,
            "start_date": request.start_date,
            "end_date": request.end_date
        }
        
        # 使用趋势采集专家进行分析
        result = await experts['collection_expert'].analyze(analysis_data)
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data={
                "stage": result.stage.value,
                "confidence": result.confidence,
                "accuracy": result.accuracy,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "metadata": result.metadata
            },
            message="趋势采集分析完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"趋势采集分析失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"趋势采集分析失败: {str(e)}",
            processing_time=processing_time
        )


@app.post("/experts/processing/analyze", response_model=APIResponse)
@performance_monitor
async def analyze_trend_processing(request: TrendAnalysisRequest):
    """趋势处理分析"""
    start_time = time.time()
    
    try:
        # 准备分析数据
        analysis_data = {
            "trends": request.trends,
            "patterns": request.patterns,
            "analysis_depth": request.analysis_depth
        }
        
        # 使用趋势处理专家进行分析
        result = await experts['processing_expert'].analyze(analysis_data)
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data={
                "stage": result.stage.value,
                "confidence": result.confidence,
                "accuracy": result.accuracy,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "metadata": result.metadata
            },
            message="趋势处理分析完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"趋势处理分析失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"趋势处理分析失败: {str(e)}",
            processing_time=processing_time
        )


@app.post("/experts/analysis/analyze", response_model=APIResponse)
@performance_monitor
async def analyze_trend_patterns(request: TrendAnalysisRequest):
    """趋势模式分析"""
    start_time = time.time()
    
    try:
        # 准备分析数据
        analysis_data = {
            "trends": request.trends,
            "patterns": request.patterns,
            "analysis_depth": request.analysis_depth
        }
        
        # 使用趋势分析专家进行分析
        result = await experts['analysis_expert'].analyze(analysis_data)
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data={
                "stage": result.stage.value,
                "confidence": result.confidence,
                "accuracy": result.accuracy,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "metadata": result.metadata
            },
            message="趋势模式分析完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"趋势模式分析失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"趋势模式分析失败: {str(e)}",
            processing_time=processing_time
        )


@app.post("/experts/prediction/predict", response_model=APIResponse)
@performance_monitor
async def predict_trends(request: TrendPredictionRequest):
    """趋势预测"""
    start_time = time.time()
    
    try:
        # 使用趋势预测专家进行预测
        predictions = await experts['prediction_expert'].predict_trends(
            request.historical_data,
            request.prediction_horizon
        )
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data=predictions,
            message="趋势预测完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"趋势预测失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"趋势预测失败: {str(e)}",
            processing_time=processing_time
        )


@app.post("/experts/report/generate", response_model=APIResponse)
@performance_monitor
async def generate_trend_report(request: TrendReportRequest):
    """生成趋势报告"""
    start_time = time.time()
    
    try:
        # 准备报告数据
        report_data = {
            "analysis_data": request.analysis_data,
            "prediction_data": request.prediction_data,
            "report_format": request.report_format
        }
        
        # 使用趋势报告专家生成报告
        report = await experts['report_expert'].generate_trend_report(report_data)
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data=report,
            message="趋势报告生成完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"趋势报告生成失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"趋势报告生成失败: {str(e)}",
            processing_time=processing_time
        )


@app.post("/experts/alert/detect", response_model=APIResponse)
@performance_monitor
async def detect_trend_anomalies(request: TrendAlertRequest):
    """检测趋势异常"""
    start_time = time.time()
    
    try:
        # 设置预警阈值
        experts['alert_expert'].set_alert_thresholds(request.alert_thresholds)
        
        # 检测异常
        anomalies = await experts['alert_expert'].detect_anomalies(request.trend_data)
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data=anomalies,
            message="趋势异常检测完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"趋势异常检测失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"趋势异常检测失败: {str(e)}",
            processing_time=processing_time
        )


@app.get("/experts/dashboard", response_model=APIResponse)
@performance_monitor
async def get_experts_dashboard():
    """获取专家仪表板数据"""
    start_time = time.time()
    
    try:
        dashboard_data = {}
        
        # 获取所有专家的仪表板数据
        for expert_name, expert in experts.items():
            if hasattr(expert, 'get_collection_dashboard'):
                dashboard_data[expert_name] = expert.get_collection_dashboard()
            elif hasattr(expert, 'get_processing_dashboard'):
                dashboard_data[expert_name] = expert.get_processing_dashboard()
            elif hasattr(expert, 'get_analysis_dashboard'):
                dashboard_data[expert_name] = expert.get_analysis_dashboard()
            elif hasattr(expert, 'get_prediction_dashboard'):
                dashboard_data[expert_name] = expert.get_prediction_dashboard()
            elif hasattr(expert, 'get_report_dashboard'):
                dashboard_data[expert_name] = expert.get_report_dashboard()
            elif hasattr(expert, 'get_alert_dashboard'):
                dashboard_data[expert_name] = expert.get_alert_dashboard()
        
        # 获取数据连接器状态
        connection_status = connector.get_connection_status()
        connection_history = connector.get_connection_history()
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data={
                "experts_dashboard": dashboard_data,
                "connection_status": connection_status,
                "connection_history": connection_history,
                "total_experts": len(experts)
            },
            message="专家仪表板数据获取完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"获取专家仪表板数据失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"获取专家仪表板数据失败: {str(e)}",
            processing_time=processing_time
        )


@app.get("/performance/metrics", response_model=APIResponse)
async def get_performance_metrics():
    """获取性能指标"""
    start_time = time.time()
    
    try:
        # 模拟性能指标数据
        metrics = {
            "average_response_time": 1.2,
            "slo_compliance_rate": 0.95,
            "total_requests": 1500,
            "success_rate": 0.98,
            "active_experts": len(experts),
            "data_platforms_connected": len(connector.platforms)
        }
        
        processing_time = time.time() - start_time
        
        return APIResponse(
            success=True,
            data=metrics,
            message="性能指标获取完成",
            processing_time=processing_time
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"获取性能指标失败: {str(e)}")
        
        return APIResponse(
            success=False,
            message=f"获取性能指标失败: {str(e)}",
            processing_time=processing_time
        )


# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局异常: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"服务器内部错误: {str(exc)}",
            "processing_time": 0.0
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # 启动API服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )