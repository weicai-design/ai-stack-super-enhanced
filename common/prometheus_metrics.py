"""
Prometheus指标收集器
为所有服务提供统一的指标收集
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from functools import wraps


# ==================== 指标定义 ====================

# HTTP请求计数器
http_requests_total = Counter(
    'http_requests_total',
    'HTTP请求总数',
    ['method', 'endpoint', 'status']
)

# HTTP请求延迟直方图
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP请求延迟（秒）',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# 活跃连接数
http_connections_active = Gauge(
    'http_connections_active',
    '当前活跃的HTTP连接数'
)

# 数据库查询计数器
db_queries_total = Counter(
    'db_queries_total',
    '数据库查询总数',
    ['operation', 'table']
)

# 数据库查询延迟
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    '数据库查询延迟（秒）',
    ['operation', 'table']
)

# AI模型推理计数器
ai_model_inferences_total = Counter(
    'ai_model_inferences_total',
    'AI模型推理总数',
    ['model', 'status']
)

# AI模型推理延迟
ai_model_inference_duration_seconds = Histogram(
    'ai_model_inference_duration_seconds',
    'AI模型推理延迟（秒）',
    ['model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# 缓存命中计数器
cache_hits_total = Counter(
    'cache_hits_total',
    '缓存命中总数',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    '缓存未命中总数',
    ['cache_type']
)

# RAG检索计数器
rag_searches_total = Counter(
    'rag_searches_total',
    'RAG检索总数',
    ['mode']  # vector, keyword, hybrid
)

# RAG文档摄入计数器
rag_documents_ingested_total = Counter(
    'rag_documents_ingested_total',
    'RAG文档摄入总数',
    ['format']
)

# 错误计数器
errors_total = Counter(
    'errors_total',
    '错误总数',
    ['error_type', 'service']
)

# 服务信息
service_info = Info(
    'service_info',
    '服务信息'
)


# ==================== 装饰器 ====================

def track_request_metrics(func):
    """跟踪HTTP请求指标的装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 获取请求信息
        request = kwargs.get('request') or (args[0] if args else None)
        
        method = request.method if request else "UNKNOWN"
        endpoint = request.url.path if request else "/"
        
        # 增加活跃连接数
        http_connections_active.inc()
        
        # 开始计时
        start_time = time.time()
        
        try:
            # 执行函数
            response = await func(*args, **kwargs)
            
            # 记录成功请求
            status = getattr(response, 'status_code', 200)
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            return response
            
        except Exception as e:
            # 记录失败请求
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()
            
            errors_total.labels(
                error_type=type(e).__name__,
                service='api'
            ).inc()
            
            raise
        
        finally:
            # 记录请求延迟
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # 减少活跃连接数
            http_connections_active.dec()
    
    return wrapper


def track_db_query(operation: str, table: str):
    """跟踪数据库查询的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                db_queries_total.labels(
                    operation=operation,
                    table=table
                ).inc()
                
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        
        return wrapper
    return decorator


def track_ai_inference(model: str):
    """跟踪AI模型推理的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                ai_model_inferences_total.labels(
                    model=model,
                    status='success'
                ).inc()
                
                return result
            
            except Exception as e:
                ai_model_inferences_total.labels(
                    model=model,
                    status='error'
                ).inc()
                raise
            
            finally:
                duration = time.time() - start_time
                ai_model_inference_duration_seconds.labels(
                    model=model
                ).observe(duration)
        
        return wrapper
    return decorator


# ==================== Metrics端点 ====================

def metrics_endpoint():
    """Metrics端点处理函数"""
    metrics_data = generate_latest()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


# ==================== 便捷函数 ====================

def record_rag_search(mode: str):
    """记录RAG检索"""
    rag_searches_total.labels(mode=mode).inc()


def record_rag_ingest(format: str):
    """记录RAG文档摄入"""
    rag_documents_ingested_total.labels(format=format).inc()


def record_cache_hit(cache_type: str):
    """记录缓存命中"""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
    """记录缓存未命中"""
    cache_misses_total.labels(cache_type=cache_type).inc()


def record_error(error_type: str, service: str):
    """记录错误"""
    errors_total.labels(error_type=error_type, service=service).inc()


def set_service_info(service_name: str, version: str, **kwargs):
    """设置服务信息"""
    info_dict = {
        'service': service_name,
        'version': version,
        **kwargs
    }
    service_info.info(info_dict)

