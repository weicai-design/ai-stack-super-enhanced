#!/usr/bin/env python3
"""
系统健康检查工具
检查所有服务状态、数据库连接、磁盘空间等
"""
import asyncio
import httpx
import psutil
import os
from datetime import datetime
from typing import Dict, Any, List


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.services = {
            'RAG系统': 'http://localhost:8011/health',
            'ERP系统': 'http://localhost:8013/health',
            '股票交易': 'http://localhost:8014/health',
            '趋势分析': 'http://localhost:8015/health',
            '内容创作': 'http://localhost:8016/health',
            '任务代理': 'http://localhost:8017/health',
            '资源管理': 'http://localhost:8018/health',
            '自我学习': 'http://localhost:8019/health',
            'AI交互中心': 'http://localhost:8020/health'
        }
        
        self.results = []
    
    async def check_service(self, name: str, url: str) -> Dict[str, Any]:
        """检查单个服务"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = datetime.now()
                response = await client.get(url)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    'name': name,
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'response_time': round(duration, 2),
                    'available': True
                }
        except Exception as e:
            return {
                'name': name,
                'status': 'down',
                'error': str(e),
                'available': False
            }
    
    async def check_all_services(self):
        """检查所有服务"""
        print("🔍 检查所有服务状态...\n")
        
        tasks = [
            self.check_service(name, url)
            for name, url in self.services.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        for result in results:
            self.results.append(result)
            
            status_icon = "✅" if result['available'] else "❌"
            status_text = result['status']
            
            if result['available']:
                response_time = result['response_time']
                print(f"{status_icon} {result['name']:<12} - {status_text:<10} ({response_time}ms)")
            else:
                print(f"{status_icon} {result['name']:<12} - {status_text}")
    
    def check_system_resources(self):
        """检查系统资源"""
        print("\n💻 检查系统资源...\n")
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = "✅" if cpu_percent < 80 else "⚠️"
        print(f"{cpu_status} CPU使用率: {cpu_percent}%")
        
        # 内存使用
        memory = psutil.virtual_memory()
        memory_status = "✅" if memory.percent < 80 else "⚠️"
        print(f"{memory_status} 内存使用: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        
        # 磁盘空间
        disk = psutil.disk_usage('/')
        disk_status = "✅" if disk.percent < 90 else "⚠️"
        print(f"{disk_status} 磁盘使用: {disk.percent}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)")
        
        # 网络连接
        net_connections = len(psutil.net_connections())
        print(f"🌐 网络连接数: {net_connections}")
    
    def check_databases(self):
        """检查数据库连接"""
        print("\n🗄️  检查数据库连接...\n")
        
        db_files = [
            'rag/vector_store.db',
            '💼 Intelligent ERP & Business Management/data/erp.db',
            '📈 Intelligent Stock Trading/data/trading.db',
            '🧠 Self Learning System/data/learning.db'
        ]
        
        for db_path in db_files:
            full_path = os.path.join('/Users/ywc/ai-stack-super-enhanced', db_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path) / 1024  # KB
                print(f"✅ {os.path.basename(db_path):<20} - {size:.1f} KB")
            else:
                print(f"⚠️  {os.path.basename(db_path):<20} - 文件不存在")
    
    def generate_report(self):
        """生成健康报告"""
        print("\n" + "=" * 60)
        print("📊 健康检查报告")
        print("=" * 60)
        
        # 服务统计
        total_services = len(self.results)
        healthy_services = sum(1 for r in self.results if r['available'])
        
        print(f"\n服务状态: {healthy_services}/{total_services} 正常运行")
        
        if healthy_services == total_services:
            print("✅ 所有服务运行正常")
        elif healthy_services > 0:
            print(f"⚠️  {total_services - healthy_services} 个服务不可用")
        else:
            print("❌ 所有服务不可用")
        
        # 平均响应时间
        available_results = [r for r in self.results if r['available']]
        if available_results:
            avg_response = sum(r['response_time'] for r in available_results) / len(available_results)
            print(f"\n平均响应时间: {avg_response:.2f}ms")
        
        # 系统资源总结
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        print(f"\n系统资源:")
        print(f"  CPU: {cpu}%")
        print(f"  内存: {memory}%")
        print(f"  磁盘: {disk}%")
        
        # 总体评估
        print("\n总体评估:")
        if healthy_services == total_services and cpu < 80 and memory < 80 and disk < 90:
            print("✅ 系统健康状况良好")
        elif healthy_services >= total_services * 0.8:
            print("⚠️  系统健康状况一般，建议检查")
        else:
            print("❌ 系统健康状况不佳，需要立即处理")
        
        print("\n生成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)


async def main():
    """主函数"""
    checker = HealthChecker()
    
    print("\n" + "=" * 60)
    print("🏥 AI Stack 系统健康检查")
    print("=" * 60 + "\n")
    
    # 检查服务
    await checker.check_all_services()
    
    # 检查系统资源
    checker.check_system_resources()
    
    # 检查数据库
    checker.check_databases()
    
    # 生成报告
    checker.generate_report()


if __name__ == "__main__":
    asyncio.run(main())




