#!/usr/bin/env python3
"""
性能分析工具
Performance Analyzer

分析系统性能，提供优化建议
"""

import time
import requests
import psutil
import statistics
from typing import List, Dict
from datetime import datetime
import json


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.results = {}
    
    def test_api_response_time(self, url: str, name: str, iterations: int = 10) -> Dict:
        """测试API响应时间"""
        response_times = []
        success_count = 0
        
        print(f"\n测试 {name}...")
        
        for i in range(iterations):
            try:
                start = time.time()
                response = requests.get(url, timeout=5)
                end = time.time()
                
                response_time = (end - start) * 1000  # 转换为毫秒
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                
                print(f"  第{i+1}次: {response_time:.2f}ms", end='\r')
            except Exception as e:
                print(f"  第{i+1}次: 失败 ({str(e)})")
        
        if response_times:
            result = {
                "name": name,
                "url": url,
                "iterations": iterations,
                "success_count": success_count,
                "success_rate": success_count / iterations,
                "avg_time": statistics.mean(response_times),
                "min_time": min(response_times),
                "max_time": max(response_times),
                "median_time": statistics.median(response_times),
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
            
            print(f"\n  ✅ 平均响应时间: {result['avg_time']:.2f}ms")
            print(f"     成功率: {result['success_rate']*100:.1f}%")
            
            return result
        else:
            return {"name": name, "error": "所有请求失败"}
    
    def analyze_system_performance(self):
        """分析系统性能"""
        print("\n" + "="*70)
        print("系统性能分析")
        print("="*70)
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        print(f"\nCPU:")
        print(f"  使用率: {cpu_percent}%")
        print(f"  核心数: {cpu_count}")
        if cpu_freq:
            print(f"  频率: {cpu_freq.current:.0f}MHz")
        
        # 内存
        memory = psutil.virtual_memory()
        print(f"\n内存:")
        print(f"  总量: {memory.total / (1024**3):.2f}GB")
        print(f"  已用: {memory.used / (1024**3):.2f}GB")
        print(f"  可用: {memory.available / (1024**3):.2f}GB")
        print(f"  使用率: {memory.percent}%")
        
        # 磁盘
        disk = psutil.disk_usage('/')
        print(f"\n磁盘:")
        print(f"  总量: {disk.total / (1024**3):.2f}GB")
        print(f"  已用: {disk.used / (1024**3):.2f}GB")
        print(f"  可用: {disk.free / (1024**3):.2f}GB")
        print(f"  使用率: {disk.percent}%")
        
        # 网络
        net_io = psutil.net_io_counters()
        print(f"\n网络:")
        print(f"  发送: {net_io.bytes_sent / (1024**2):.2f}MB")
        print(f"  接收: {net_io.bytes_recv / (1024**2):.2f}MB")
        
        return {
            "cpu": {"percent": cpu_percent, "count": cpu_count},
            "memory": {"percent": memory.percent, "available_gb": memory.available / (1024**3)},
            "disk": {"percent": disk.percent, "free_gb": disk.free / (1024**3)}
        }
    
    def benchmark_apis(self):
        """基准测试APIs"""
        print("\n" + "="*70)
        print("API性能基准测试")
        print("="*70)
        
        apis = [
            ("http://localhost:8013/health", "ERP健康检查"),
            ("http://localhost:8013/api/info", "ERP API信息"),
            ("http://localhost:8013/api/finance/dashboard?period_type=monthly", "财务看板"),
            ("http://localhost:8013/api/business/customers", "客户列表"),
            ("http://localhost:8013/api/material/materials", "物料列表"),
            ("http://localhost:8013/api/production/orders", "生产订单"),
            ("http://localhost:8020/health", "命令网关"),
        ]
        
        results = []
        for url, name in apis:
            result = self.test_api_response_time(url, name, iterations=10)
            results.append(result)
        
        return results
    
    def generate_performance_report(self, api_results: List[Dict], system_perf: Dict):
        """生成性能报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_performance": system_perf,
            "api_performance": api_results,
            "recommendations": self._generate_recommendations(api_results, system_perf)
        }
        
        # 保存JSON报告
        report_path = "/Users/ywc/ai-stack-super-enhanced/performance_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 生成Markdown报告
        md_report = self._generate_markdown_report(report)
        md_path = "/Users/ywc/ai-stack-super-enhanced/📊性能分析报告.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)
        
        print(f"\n✅ 性能报告已生成:")
        print(f"   JSON: performance_report.json")
        print(f"   Markdown: 📊性能分析报告.md")
        
        return report
    
    def _generate_recommendations(self, api_results: List[Dict], system_perf: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # CPU建议
        if system_perf['cpu']['percent'] > 80:
            recommendations.append("CPU使用率过高，建议优化计算密集型任务或增加CPU资源")
        
        # 内存建议
        if system_perf['memory']['percent'] > 85:
            recommendations.append("内存使用率过高，建议优化内存使用或增加内存")
        
        # 磁盘建议
        if system_perf['disk']['percent'] > 90:
            recommendations.append("磁盘空间不足，建议清理无用文件或扩展存储")
        
        # API响应时间建议
        slow_apis = [api for api in api_results if api.get('avg_time', 0) > 500]
        if slow_apis:
            for api in slow_apis:
                recommendations.append(f"API '{api['name']}' 响应时间过长({api['avg_time']:.0f}ms)，建议优化")
        
        # 成功率建议
        failing_apis = [api for api in api_results if api.get('success_rate', 1) < 0.9]
        if failing_apis:
            for api in failing_apis:
                recommendations.append(f"API '{api['name']}' 成功率过低({api['success_rate']*100:.0f}%)，建议检查")
        
        if not recommendations:
            recommendations.append("系统性能良好，暂无优化建议 ✅")
        
        return recommendations
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成Markdown格式报告"""
        md = f"""# 📊 系统性能分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**系统版本**: v2.0.1  

---

## 🖥️ 系统资源使用

| 资源 | 使用率 | 可用量 | 状态 |
|------|--------|--------|------|
| CPU | {report['system_performance']['cpu']['percent']}% | {report['system_performance']['cpu']['count']}核 | {'⚠️ 偏高' if report['system_performance']['cpu']['percent'] > 70 else '✅ 正常'} |
| 内存 | {report['system_performance']['memory']['percent']}% | {report['system_performance']['memory']['available_gb']:.2f}GB | {'⚠️ 偏高' if report['system_performance']['memory']['percent'] > 70 else '✅ 正常'} |
| 磁盘 | {report['system_performance']['disk']['percent']}% | {report['system_performance']['disk']['free_gb']:.2f}GB | {'⚠️ 偏低' if report['system_performance']['disk']['percent'] > 80 else '✅ 充足'} |

---

## ⚡ API性能测试

| API | 平均响应 | 最小 | 最大 | 成功率 | 评价 |
|-----|---------|------|------|--------|------|
"""
        
        for api in report['api_performance']:
            if 'avg_time' in api:
                status = '✅ 优秀' if api['avg_time'] < 100 else ('⚠️ 一般' if api['avg_time'] < 500 else '❌ 慢')
                md += f"| {api['name']} | {api['avg_time']:.0f}ms | {api['min_time']:.0f}ms | {api['max_time']:.0f}ms | {api['success_rate']*100:.0f}% | {status} |\n"
        
        md += f"""
---

## 💡 优化建议

"""
        for i, rec in enumerate(report['recommendations'], 1):
            md += f"{i}. {rec}\n"
        
        md += f"""
---

## 📊 性能评级

"""
        
        avg_response_time = statistics.mean([api['avg_time'] for api in report['api_performance'] if 'avg_time' in api])
        
        if avg_response_time < 100:
            grade = "A+ (优秀)"
        elif avg_response_time < 200:
            grade = "A (良好)"
        elif avg_response_time < 500:
            grade = "B (一般)"
        else:
            grade = "C (需优化)"
        
        md += f"**平均响应时间**: {avg_response_time:.2f}ms  \n"
        md += f"**性能评级**: {grade}  \n\n"
        
        md += "---\n\n**分析完成** ✅\n"
        
        return md
    
    def run_full_analysis(self):
        """运行完整性能分析"""
        print("\n" + "="*70)
        print("AI Stack Super Enhanced - 性能分析工具")
        print("="*70)
        
        # 系统性能
        system_perf = self.analyze_system_performance()
        
        # API基准测试
        api_results = self.benchmark_apis()
        
        # 生成报告
        report = self.generate_performance_report(api_results, system_perf)
        
        # 打印建议
        print("\n" + "="*70)
        print("优化建议")
        print("="*70 + "\n")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
        
        return report


if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    analyzer.run_full_analysis()

