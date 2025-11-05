#!/usr/bin/env python3
"""
AI Stack Super Enhanced - 性能测试工具
功能：测试所有服务的API响应时间和系统资源使用
"""

import requests
import time
import psutil
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ServiceTest:
    name: str
    url: str
    response_time: float = 0.0
    status_code: int = 0
    success: bool = False
    error: str = ""

class PerformanceTester:
    def __init__(self):
        self.services = [
            ("OpenWebUI", "http://localhost:3000"),
            ("RAG系统", "http://localhost:8011/health"),
            ("ERP前端", "http://localhost:8012"),
            ("ERP后端", "http://localhost:8013/health"),
            ("股票交易", "http://localhost:8014/health"),
            ("趋势分析", "http://localhost:8015/health"),
            ("内容创作", "http://localhost:8016/health"),
            ("任务代理", "http://localhost:8017/health"),
            ("资源管理", "http://localhost:8018/health"),
            ("自我学习", "http://localhost:8019/health"),
        ]
        
    def test_service_response(self, name: str, url: str) -> ServiceTest:
        """测试单个服务的响应时间"""
        test = ServiceTest(name=name, url=url)
        
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            end = time.time()
            
            test.response_time = (end - start) * 1000  # 转换为毫秒
            test.status_code = response.status_code
            test.success = response.status_code == 200
            
        except Exception as e:
            test.error = str(e)
            test.success = False
            
        return test
        
    def get_system_metrics(self) -> Dict:
        """获取系统资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_total_gb': disk.total / (1024**3),
        }
        
    def run_tests(self, iterations: int = 3) -> Dict:
        """运行性能测试"""
        print(f"\n🔬 AI Stack 性能测试")
        print(f"测试轮数: {iterations}")
        print("=" * 60)
        
        all_results = []
        
        for i in range(iterations):
            print(f"\n第 {i+1}/{iterations} 轮测试...")
            round_results = []
            
            for name, url in self.services:
                result = self.test_service_response(name, url)
                round_results.append(result)
                
                status = "✅" if result.success else "❌"
                time_str = f"{result.response_time:.1f}ms" if result.success else "N/A"
                print(f"  {status} {name:15} {time_str}")
                
            all_results.append(round_results)
            
            if i < iterations - 1:
                time.sleep(1)
        
        # 计算统计数据
        stats = self.calculate_statistics(all_results)
        
        # 获取系统资源
        system_metrics = self.get_system_metrics()
        
        return {
            'iterations': iterations,
            'statistics': stats,
            'system_metrics': system_metrics,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    def calculate_statistics(self, all_results: List[List[ServiceTest]]) -> Dict:
        """计算性能统计数据"""
        stats = {}
        
        for i, (name, _) in enumerate(self.services):
            response_times = []
            success_count = 0
            
            for round_results in all_results:
                result = round_results[i]
                if result.success:
                    response_times.append(result.response_time)
                    success_count += 1
            
            if response_times:
                stats[name] = {
                    'avg_response_time': sum(response_times) / len(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'success_rate': success_count / len(all_results) * 100
                }
            else:
                stats[name] = {
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'success_rate': 0
                }
                
        return stats
        
    def print_report(self, results: Dict):
        """打印性能报告"""
        print("\n" + "=" * 60)
        print("📊 性能测试报告")
        print("=" * 60)
        
        stats = results['statistics']
        
        print("\n🚀 API响应时间统计:")
        print("-" * 60)
        print(f"{'服务':<15} {'平均':<12} {'最小':<12} {'最大':<12} {'成功率'}")
        print("-" * 60)
        
        for name, data in stats.items():
            avg = f"{data['avg_response_time']:.1f}ms"
            min_t = f"{data['min_response_time']:.1f}ms"
            max_t = f"{data['max_response_time']:.1f}ms"
            success = f"{data['success_rate']:.0f}%"
            print(f"{name:<15} {avg:<12} {min_t:<12} {max_t:<12} {success}")
        
        # 系统资源
        metrics = results['system_metrics']
        print("\n💻 系统资源使用:")
        print("-" * 60)
        print(f"CPU使用率:     {metrics['cpu_percent']:.1f}%")
        print(f"内存使用率:    {metrics['memory_percent']:.1f}%")
        print(f"内存使用:      {metrics['memory_used_gb']:.2f}GB / {metrics['memory_total_gb']:.2f}GB")
        print(f"磁盘使用率:    {metrics['disk_percent']:.1f}%")
        print(f"磁盘使用:      {metrics['disk_used_gb']:.1f}GB / {metrics['disk_total_gb']:.1f}GB")
        
        # 性能评级
        avg_response_times = [s['avg_response_time'] for s in stats.values() if s['avg_response_time'] > 0]
        if avg_response_times:
            overall_avg = sum(avg_response_times) / len(avg_response_times)
            
            print("\n⭐ 性能评级:")
            print("-" * 60)
            print(f"平均响应时间: {overall_avg:.1f}ms")
            
            if overall_avg < 100:
                rating = "⭐⭐⭐⭐⭐ 优秀"
            elif overall_avg < 200:
                rating = "⭐⭐⭐⭐ 良好"
            elif overall_avg < 500:
                rating = "⭐⭐⭐ 一般"
            else:
                rating = "⭐⭐ 需要优化"
                
            print(f"性能评级: {rating}")
        
        print("\n" + "=" * 60)
        print(f"测试时间: {results['timestamp']}")
        print("=" * 60)
        
    def save_results(self, results: Dict, filename: str = "performance_report.json"):
        """保存测试结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 测试结果已保存: {filename}")

def main():
    tester = PerformanceTester()
    
    # 运行测试
    results = tester.run_tests(iterations=3)
    
    # 打印报告
    tester.print_report(results)
    
    # 保存结果
    tester.save_results(results)

if __name__ == "__main__":
    main()

