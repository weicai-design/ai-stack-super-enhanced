"""
ERP系统性能优化工具
用于监控和优化系统性能
"""

import time
import requests
import statistics
from typing import List, Dict
from datetime import datetime


class PerformanceOptimizer:
    """性能优化工具"""
    
    def __init__(self, base_url: str = "http://localhost:8013"):
        self.base_url = base_url
        self.performance_data = []
    
    def benchmark_api_performance(
        self,
        endpoint: str,
        iterations: int = 100
    ) -> Dict:
        """
        API性能基准测试
        
        Args:
            endpoint: API端点
            iterations: 测试次数
        
        Returns:
            性能统计
        """
        print(f"\n🔬 测试API: {endpoint}")
        print(f"   测试次数: {iterations}")
        
        response_times = []
        success_count = 0
        error_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
                
                response_times.append(elapsed)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                elapsed = 10000  # 超时记为10秒
                response_times.append(elapsed)
            
            # 进度显示
            if (i + 1) % 10 == 0:
                print(f"   进度: {i+1}/{iterations}")
        
        # 计算统计数据
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            
            # 性能评级
            if avg_time < 50:
                grade = "A+优秀"
                color = "green"
            elif avg_time < 100:
                grade = "A良好"
                color = "blue"
            elif avg_time < 200:
                grade = "B一般"
                color = "yellow"
            else:
                grade = "C需优化"
                color = "red"
        else:
            avg_time = median_time = min_time = max_time = p95_time = 0
            grade = "F失败"
            color = "red"
        
        result = {
            "endpoint": endpoint,
            "iterations": iterations,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round((success_count / iterations * 100), 2),
            "response_times_ms": {
                "average": round(avg_time, 2),
                "median": round(median_time, 2),
                "min": round(min_time, 2),
                "max": round(max_time, 2),
                "p95": round(p95_time, 2)
            },
            "performance_grade": grade,
            "color": color
        }
        
        # 打印结果
        print(f"\n   ✅ 测试完成:")
        print(f"   成功率: {result['success_rate']}%")
        print(f"   平均响应: {result['response_times_ms']['average']}ms")
        print(f"   中位数: {result['response_times_ms']['median']}ms")
        print(f"   P95: {result['response_times_ms']['p95']}ms")
        print(f"   性能评级: {result['performance_grade']}")
        
        self.performance_data.append(result)
        return result
    
    def test_all_endpoints(self) -> Dict:
        """测试所有主要端点"""
        print("\n" + "="*70)
        print("  🚀 ERP系统性能基准测试")
        print("="*70)
        
        # 定义要测试的端点
        endpoints = [
            "/health",
            "/api/info",
            "/api/advanced/status",
            "/api/advanced/summary",
            "/api/advanced/capabilities"
        ]
        
        results = []
        
        for endpoint in endpoints:
            result = self.benchmark_api_performance(endpoint, iterations=50)
            results.append(result)
            time.sleep(1)  # 间隔1秒
        
        # 生成汇总报告
        self.generate_performance_report(results)
        
        return {
            "test_time": datetime.now().isoformat(),
            "total_endpoints_tested": len(endpoints),
            "results": results
        }
    
    def generate_performance_report(self, results: List[Dict]):
        """生成性能报告"""
        print("\n" + "="*70)
        print("  📊 性能测试报告")
        print("="*70)
        
        # 计算总体统计
        total_requests = sum(r['iterations'] for r in results)
        total_success = sum(r['success_count'] for r in results)
        avg_response_times = [r['response_times_ms']['average'] for r in results]
        overall_avg = statistics.mean(avg_response_times)
        
        print(f"\n总体统计:")
        print(f"  总请求数: {total_requests}")
        print(f"  成功数: {total_success}")
        print(f"  成功率: {(total_success/total_requests*100):.2f}%")
        print(f"  平均响应时间: {overall_avg:.2f}ms")
        
        # 按性能分级
        excellent = sum(1 for r in results if r['response_times_ms']['average'] < 50)
        good = sum(1 for r in results if 50 <= r['response_times_ms']['average'] < 100)
        average = sum(1 for r in results if 100 <= r['response_times_ms']['average'] < 200)
        poor = sum(1 for r in results if r['response_times_ms']['average'] >= 200)
        
        print(f"\n性能分级:")
        print(f"  A+优秀 (<50ms): {excellent}")
        print(f"  A良好 (50-100ms): {good}")
        print(f"  B一般 (100-200ms): {average}")
        print(f"  C需优化 (>200ms): {poor}")
        
        # 识别慢接口
        slow_endpoints = [r for r in results if r['response_times_ms']['average'] > 200]
        
        if slow_endpoints:
            print(f"\n⚠️  慢接口识别:")
            for endpoint in slow_endpoints:
                print(f"  - {endpoint['endpoint']}: {endpoint['response_times_ms']['average']}ms")
                print(f"    建议: 优化数据库查询或添加缓存")
        else:
            print(f"\n✅ 所有接口性能良好！")
        
        # 总体评估
        if overall_avg < 100:
            assessment = "系统性能优秀 ⭐⭐⭐"
        elif overall_avg < 200:
            assessment = "系统性能良好 ⭐⭐"
        else:
            assessment = "系统需要优化 ⭐"
        
        print(f"\n🎯 总体评估: {assessment}")
        print("="*70 + "\n")
    
    def optimize_database(self):
        """数据库优化"""
        print("\n🔧 优化数据库...")
        
        import sqlite3
        
        try:
            conn = sqlite3.connect('erp_data.db')
            cursor = conn.cursor()
            
            # VACUUM优化
            print("   执行VACUUM...")
            cursor.execute("VACUUM;")
            
            # ANALYZE统计
            print("   执行ANALYZE...")
            cursor.execute("ANALYZE;")
            
            conn.commit()
            conn.close()
            
            print("   ✅ 数据库优化完成")
            
        except Exception as e:
            print(f"   ❌ 优化失败: {e}")
    
    def check_system_health(self):
        """系统健康检查"""
        print("\n🏥 系统健康检查...")
        
        checks = []
        
        # 1. 服务可用性
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                checks.append(("服务可用性", True, "✅"))
            else:
                checks.append(("服务可用性", False, f"❌ 状态码{response.status_code}"))
        except:
            checks.append(("服务可用性", False, "❌ 无法连接"))
        
        # 2. 数据库连接
        try:
            import sqlite3
            conn = sqlite3.connect('erp_data.db', timeout=1)
            conn.execute("SELECT 1")
            conn.close()
            checks.append(("数据库连接", True, "✅"))
        except:
            checks.append(("数据库连接", False, "❌"))
        
        # 3. 高级功能
        try:
            response = requests.get(f"{self.base_url}/api/advanced/status", timeout=5)
            data = response.json()
            if data.get('advanced_modules_available'):
                checks.append(("高级功能", True, "✅"))
            else:
                checks.append(("高级功能", False, "⚠️  部分不可用"))
        except:
            checks.append(("高级功能", False, "❌"))
        
        # 4. 磁盘空间
        import shutil
        disk_usage = shutil.disk_usage('.')
        free_gb = disk_usage.free / (1024**3)
        if free_gb > 1:
            checks.append(("磁盘空间", True, f"✅ 剩余{free_gb:.1f}GB"))
        else:
            checks.append(("磁盘空间", False, f"⚠️  仅剩{free_gb:.1f}GB"))
        
        # 打印结果
        print("\n检查结果:")
        for name, status, message in checks:
            print(f"  {name}: {message}")
        
        # 总体状态
        all_ok = all(c[1] for c in checks)
        if all_ok:
            print("\n🎉 系统健康状况良好！")
        else:
            print("\n⚠️  发现一些问题，请检查上述项目")
        
        return checks


def main():
    """主函数"""
    print("\n╔" + "="*68 + "╗")
    print("║" + " "*18 + "ERP性能优化工具" + " "*19 + "║")
    print("╚" + "="*68 + "╝\n")
    
    optimizer = PerformanceOptimizer()
    
    # 菜单
    print("请选择操作:")
    print("1. 系统健康检查")
    print("2. API性能测试")
    print("3. 数据库优化")
    print("4. 完整诊断（包括1+2+3）")
    print("0. 退出")
    
    choice = input("\n请输入选项 (0-4): ").strip()
    
    if choice == "1":
        optimizer.check_system_health()
    elif choice == "2":
        optimizer.test_all_endpoints()
    elif choice == "3":
        optimizer.optimize_database()
    elif choice == "4":
        print("\n开始完整诊断...\n")
        optimizer.check_system_health()
        optimizer.test_all_endpoints()
        optimizer.optimize_database()
        print("\n✅ 完整诊断完成！")
    elif choice == "0":
        print("退出")
    else:
        print("无效选项")


if __name__ == "__main__":
    main()


