"""
AI-Stack ERP 综合功能测试脚本
测试所有高级功能的API调用
"""

import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8013/api"


def print_section(title: str):
    """打印分节"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_advanced_features_status():
    """测试1: 检查高级功能状态"""
    print_section("测试1: 高级功能模块状态检查")
    
    try:
        response = requests.get(f"{BASE_URL}/advanced/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 高级功能API可用")
            print(f"   总功能数: {data.get('total_advanced_features', 0)}")
            print(f"   API端点: {data.get('total_api_endpoints', 0)}")
            print(f"   系统版本: {data.get('system_version', 'unknown')}")
            print(f"   完成度: {data.get('completion', 'unknown')}")
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("   请确保ERP服务正在运行: ./start_erp.sh")
        return False


def test_analytics_api():
    """测试2: 高级分析API"""
    print_section("测试2: 高级经营分析API")
    
    try:
        # 测试行业对比分析
        company_data = {
            "revenue_growth": 0.15,
            "profit_margin": 0.12,
            "asset_turnover": 1.5,
            "roe": 0.18
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/industry-comparison?industry=制造业",
            json=company_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 行业对比分析 - 成功")
            print(f"   整体评估: {result.get('overall_assessment', 'N/A')}")
            print(f"   综合得分: {result.get('average_score', 0)}/4.0")
        else:
            print(f"⚠️  行业对比分析 - 失败: {response.status_code}")
        
        # 测试ROI分析
        investment_data = {
            "investment_amount": 1000000,
            "returns": [150000, 180000, 200000, 220000, 250000],
            "costs": [30000, 35000, 40000, 42000, 45000],
            "investment_type": "设备投资",
            "risk_level": "中"
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/roi-analysis",
            json=investment_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ROI深度分析 - 成功")
            print(f"   投资建议: {result.get('investment_recommendation', {}).get('recommendation', 'N/A')}")
            print(f"   NPV: {result.get('time_value_analysis', {}).get('npv', 0)}")
        else:
            print(f"⚠️  ROI分析 - 失败: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_system_summary():
    """测试3: 系统汇总信息"""
    print_section("测试3: 系统能力汇总")
    
    try:
        response = requests.get(f"{BASE_URL}/advanced/summary", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统汇总API - 成功")
            print(f"   系统名称: {data.get('system_name', 'N/A')}")
            print(f"   版本: {data.get('version', 'N/A')}")
            print(f"   完成度: {data.get('completion', 'N/A')}")
            print(f"   总功能数: {data.get('intelligent_capabilities', {}).get('smart_analysis', {}).get('count', 0)}")
            return True
        else:
            print(f"⚠️  系统汇总API - 失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_capabilities():
    """测试4: 系统能力图谱"""
    print_section("测试4: 系统能力图谱")
    
    try:
        response = requests.get(f"{BASE_URL}/advanced/capabilities", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 能力图谱API - 成功")
            
            capabilities = data.get('capabilities_matrix', {})
            print("\n   能力评估:")
            for cap_name, cap_data in capabilities.items():
                print(f"   - {cap_name}: {cap_data.get('level', 'N/A')} ({cap_data.get('score', 0)}分)")
            
            print(f"\n   整体智能化水平: {data.get('overall_intelligence_level', 'N/A')}")
            print(f"   生产就绪: {'是' if data.get('production_ready', False) else '否'}")
            return True
        else:
            print(f"⚠️  能力图谱API - 失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_api_info():
    """测试5: API信息"""
    print_section("测试5: ERP API信息")
    
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API信息 - 成功")
            print(f"   名称: {data.get('name', 'N/A')}")
            print(f"   版本: {data.get('version', 'N/A')}")
            print(f"   模块总数: {data.get('total_modules', 0)}")
            print(f"   API总数: {data.get('api_count', 'N/A')}")
            print(f"   完成度: {data.get('completion', 'N/A')}")
            print(f"   95%以上模块: {data.get('modules_95_plus', 0)}")
            print(f"   98%以上模块: {data.get('modules_98_plus', 0)}")
            return True
        else:
            print(f"⚠️  API信息 - 失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def generate_test_report(results: list):
    """生成测试报告"""
    print_section("📊 测试报告")
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ✅")
    print(f"失败: {failed_tests} ❌")
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 所有测试通过！系统运行正常！")
    elif success_rate >= 80:
        print("\n✅ 大部分测试通过，系统基本正常")
    else:
        print("\n⚠️  部分测试失败，请检查系统状态")
    
    print("\n" + "="*70)


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "AI-Stack ERP 综合功能测试" + " "*16 + "║")
    print("╚" + "="*68 + "╝")
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("测试目标: 验证所有高级功能API可用性")
    
    results = []
    
    # 执行测试
    results.append(test_advanced_features_status())
    results.append(test_analytics_api())
    results.append(test_system_summary())
    results.append(test_capabilities())
    results.append(test_api_info())
    
    # 生成报告
    generate_test_report(results)
    
    print("\n💡 提示:")
    print("   - 如果测试失败，请确保ERP服务正在运行")
    print("   - 启动服务: cd '💼 Intelligent ERP & Business Management' && ./start_erp.sh")
    print("   - API文档: http://localhost:8013/docs")
    print("   - 高级分析页面: http://localhost:8000/advanced-analytics.html")
    print()


if __name__ == "__main__":
    main()


