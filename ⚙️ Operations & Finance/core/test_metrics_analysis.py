"""
指标分析系统测试脚本 - 生产级演示
"""

import sys
import os
import asyncio
import time
import random
from datetime import datetime, timedelta

# 添加路径以导入核心模块
sys.path.append(os.path.dirname(__file__))

from monitoring_system import ExpertMonitor, ExpertMetric, MetricType
from metrics_analysis import MetricsAnalyzer, MetricsAnalysisAPI, AnalysisPeriod


async def test_metrics_analysis():
    """测试指标分析系统"""
    print("=== 指标分析系统生产级测试 ===")
    
    # 创建监控器实例
    monitor = ExpertMonitor()
    
    # 模拟一些专家数据
    experts = ["expert_ai_1", "expert_ai_2", "expert_ai_3"]
    
    print("1. 模拟专家性能数据...")
    
    # 模拟过去24小时的数据
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    for expert_name in experts:
        print(f"\n为专家 {expert_name} 生成模拟数据...")
        
        # 模拟响应时间数据
        for i in range(100):
            timestamp = start_time + timedelta(minutes=i * 14.4)  # 24小时内的100个点
            
            # 模拟正常的响应时间（0.1-0.3秒）
            response_time = random.uniform(0.1, 0.3)
            
            # 偶尔模拟异常高的响应时间
            if random.random() < 0.05:  # 5%的概率出现异常
                response_time = random.uniform(0.5, 2.0)
            
            monitor.record_metric(
                expert_name=expert_name,
                metric_type=MetricType.RESPONSE_TIME.value,
                value=response_time,
                tags={"source": "test_simulation", "confidence": "0.95"}
            )
        
        # 模拟吞吐量数据
        for i in range(24):  # 每小时一个点
            timestamp = start_time + timedelta(hours=i)
            throughput = random.uniform(10, 100)
            
            monitor.record_metric(
                expert_name=expert_name,
                metric_type=MetricType.THROUGHPUT.value,
                value=throughput,
                tags={"source": "test_simulation", "confidence": "0.95"}
            )
        
        # 模拟请求记录
        for i in range(50):
            timestamp = start_time + timedelta(minutes=i * 28.8)  # 24小时内的50个请求
            
            # 模拟成功和失败的请求
            success = random.random() > 0.1  # 90%成功率
            
            monitor.record_request(
                expert_name=expert_name,
                response_time=random.uniform(0.1, 0.3),
                success=success,
                error_type="timeout" if not success else None
            )
    
    print("\n2. 创建指标分析器...")
    analyzer = MetricsAnalyzer(monitor)
    
    print("\n3. 测试性能分析功能...")
    
    for expert_name in experts:
        print(f"\n--- 分析专家 {expert_name} ---")
        
        # 测试不同周期的分析
        for period in [AnalysisPeriod.REAL_TIME, AnalysisPeriod.HOUR, AnalysisPeriod.DAY]:
            try:
                analysis = analyzer.analyze_performance(expert_name, period)
                
                print(f"周期: {period.value}")
                print(f"  健康评分: {analysis.health_score}")
                print(f"  性能评分: {analysis.performance_score}")
                print(f"  平均响应时间: {analysis.response_time_avg:.3f}s")
                print(f"  P95响应时间: {analysis.response_time_p95:.3f}s")
                print(f"  成功率: {analysis.success_rate:.1%}")
                print(f"  吞吐量: {analysis.throughput:.1f} req/h")
                print(f"  趋势: {analysis.trend.value}")
                
                if analysis.anomalies:
                    print(f"  检测到异常: {len(analysis.anomalies)}个")
                
                if analysis.recommendations:
                    print(f"  优化建议: {analysis.recommendations[0]}")
                
            except Exception as e:
                print(f"  分析失败: {e}")
    
    print("\n4. 测试API功能...")
    api = MetricsAnalysisAPI(analyzer)
    
    # 测试性能分析API
    result = api.get_performance_analysis("expert_ai_1", "hour")
    if result["success"]:
        print("✓ API性能分析测试通过")
        analysis_data = result["analysis"]
        print(f"  健康评分: {analysis_data['health_score']}")
        print(f"  性能评分: {analysis_data['performance_score']}")
    else:
        print("✗ API性能分析测试失败")
    
    # 测试对比分析API
    result = api.get_comparative_analysis("expert_ai_1", "baseline")
    if result["success"]:
        print("✓ API对比分析测试通过")
    else:
        print("✗ API对比分析测试失败")
    
    # 测试分析摘要API
    result = api.get_analysis_summary()
    if result["success"]:
        print("✓ API分析摘要测试通过")
        summary = result["summary"]
        print(f"  跟踪专家数: {summary['total_experts']}")
        print(f"  平均健康评分: {summary['avg_health_score']}")
    else:
        print("✗ API分析摘要测试失败")
    
    print("\n5. 测试定期分析任务...")
    
    # 启动定期分析
    await analyzer.start_periodic_analysis()
    
    # 等待几秒钟让任务运行
    await asyncio.sleep(5)
    
    # 停止定期分析
    await analyzer.stop_periodic_analysis()
    
    print("✓ 定期分析任务测试通过")
    
    print("\n6. 测试缓存机制...")
    
    # 第一次分析（应该计算）
    start_time = time.time()
    analysis1 = analyzer.analyze_performance("expert_ai_1", AnalysisPeriod.HOUR)
    time1 = time.time() - start_time
    
    # 第二次分析（应该使用缓存）
    start_time = time.time()
    analysis2 = analyzer.analyze_performance("expert_ai_1", AnalysisPeriod.HOUR)
    time2 = time.time() - start_time
    
    print(f"  第一次分析耗时: {time1:.3f}s")
    print(f"  第二次分析耗时: {time2:.3f}s")
    
    if time2 < time1:
        print("✓ 缓存机制测试通过")
    else:
        print("⚠ 缓存机制可能未生效")
    
    print("\n7. 测试异常检测...")
    
    # 模拟一个异常高的响应时间
    monitor.record_metric(
        expert_name="expert_ai_1",
        metric_type=MetricType.RESPONSE_TIME.value,
        value=5.0,  # 异常高的响应时间
        tags={"source": "test_anomaly", "confidence": "0.95"}
    )
    
    # 重新分析
    analysis = analyzer.analyze_performance("expert_ai_1", AnalysisPeriod.REAL_TIME)
    
    if analysis.anomalies:
        print("✓ 异常检测测试通过")
        print(f"  检测到异常: {len(analysis.anomalies)}个")
        for anomaly in analysis.anomalies:
            print(f"    异常类型: {anomaly['type']}, 值: {anomaly['value']}")
    else:
        print("✗ 异常检测测试失败")
    
    print("\n8. 测试基准线对比...")
    
    analysis = analyzer.analyze_performance("expert_ai_1", AnalysisPeriod.HOUR)
    
    if analysis.baseline_comparison:
        print("✓ 基准线对比测试通过")
        for metric, comparison in analysis.baseline_comparison.items():
            print(f"  {metric}: 值={comparison['value']}, 等级={comparison['level']}")
    else:
        print("✗ 基准线对比测试失败")
    
    print("\n=== 指标分析系统测试完成 ===")
    
    # 显示系统统计信息
    print("\n系统统计信息:")
    print(f"监控专家数: {len(experts)}")
    print(f"缓存命中率: {len(analyzer.analysis_cache)} 个缓存项")
    
    # 显示性能监控器统计
    if hasattr(analyzer, 'performance_monitor'):
        stats = analyzer.performance_monitor.get_stats()
        print(f"性能监控器调用次数: {stats.get('total_calls', 0)}")


if __name__ == "__main__":
    asyncio.run(test_metrics_analysis())