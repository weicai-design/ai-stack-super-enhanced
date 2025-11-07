"""
高级经营分析模块使用示例
展示4个核心分析器的实际应用场景
"""

import sys
from pathlib import Path
import json

# 添加当前目录到路径
sys.path.append(str(Path(__file__).parent))

from industry_comparator import industry_comparator
from roi_deep_analyzer import roi_deep_analyzer
from key_factor_identifier import key_factor_identifier
from long_term_predictor import long_term_predictor


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def example_1_industry_comparison():
    """示例1: 行业对比分析"""
    print_section("示例1: 行业对比分析")
    
    # 公司数据
    company_data = {
        "revenue_growth": 0.15,      # 营收增长率 15%
        "profit_margin": 0.12,       # 利润率 12%
        "asset_turnover": 1.5,       # 资产周转率 1.5
        "roe": 0.18,                 # 股东权益回报率 18%
        "current_ratio": 1.8,        # 流动比率 1.8
        "debt_ratio": 0.45           # 负债率 45%
    }
    
    print("📊 公司数据:")
    print(json.dumps(company_data, indent=2, ensure_ascii=False))
    
    # 执行对比分析
    result = industry_comparator.compare_with_industry(
        company_data=company_data,
        industry="制造业"
    )
    
    print(f"\n🏭 行业: {result['industry']}")
    print(f"📈 整体评估: {result['overall_assessment']}")
    print(f"⭐ 综合得分: {result['average_score']}/4.0")
    
    print("\n📋 详细对比:")
    for metric, data in result['comparison'].items():
        print(f"\n  {metric}:")
        print(f"    公司值: {data['company_value']}")
        print(f"    行业平均: {data['industry_average']}")
        print(f"    差异: {data['difference_percent']}%")
        print(f"    表现: {data['performance']} ({data['grade']}级)")
    
    print("\n" + "-"*70)
    print("💡 建议:")
    print("  - 继续保持营收增长的优势")
    print("  - 关注利润率提升")
    print("  - 优化资产运营效率")
    

def example_2_competitive_position():
    """示例2: 竞争地位分析"""
    print_section("示例2: 竞争地位分析")
    
    # 我司数据
    company_data = {
        "revenue_growth": 0.15,
        "profit_margin": 0.12,
        "asset_turnover": 1.5,
        "roe": 0.18
    }
    
    # 竞争对手数据
    competitors_data = [
        {
            "revenue_growth": 0.10,
            "profit_margin": 0.10,
            "asset_turnover": 1.2,
            "roe": 0.15
        },
        {
            "revenue_growth": 0.12,
            "profit_margin": 0.11,
            "asset_turnover": 1.3,
            "roe": 0.16
        },
        {
            "revenue_growth": 0.08,
            "profit_margin": 0.09,
            "asset_turnover": 1.1,
            "roe": 0.14
        }
    ]
    
    print(f"📊 分析对象: 我司 + {len(competitors_data)}家竞争对手")
    
    result = industry_comparator.analyze_competitive_position(
        company_data=company_data,
        competitors_data=competitors_data,
        industry="制造业"
    )
    
    print(f"\n🏆 竞争地位: {result['competitive_position']}")
    print(f"📊 平均排名: {result['average_rank']}/{len(competitors_data) + 1}")
    
    print("\n📋 各指标排名:")
    for metric, ranking in result['rankings_by_metric'].items():
        print(f"\n  {metric}:")
        print(f"    排名: {ranking['rank']}/{ranking['total_companies']}")
        print(f"    百分位: {ranking['percentile']}%")


def example_3_roi_analysis():
    """示例3: ROI深度分析"""
    print_section("示例3: ROI深度分析 - 设备投资评估")
    
    # 投资数据
    investment_data = {
        "investment_amount": 1000000,  # 投资100万
        "returns": [150000, 180000, 200000, 220000, 250000],  # 5年收益
        "costs": [30000, 35000, 40000, 42000, 45000],  # 5年成本
        "time_periods": ["Year1", "Year2", "Year3", "Year4", "Year5"],
        "investment_type": "设备投资",
        "risk_level": "中",
        "efficiency_improvement": 15,
        "quality_improvement": 10,
        "market_expansion": 8
    }
    
    print("💰 投资概况:")
    print(f"  投资金额: ¥{investment_data['investment_amount']:,}")
    print(f"  投资类型: {investment_data['investment_type']}")
    print(f"  风险等级: {investment_data['risk_level']}")
    
    # 执行ROI分析
    result = roi_deep_analyzer.analyze_roi_comprehensive(investment_data)
    
    # 基础ROI
    basic_roi = result['basic_roi']
    print(f"\n📊 基础ROI分析:")
    print(f"  总收益: ¥{basic_roi['total_returns']:,}")
    print(f"  总成本: ¥{basic_roi['total_costs']:,}")
    print(f"  净收益: ¥{basic_roi['net_returns']:,}")
    print(f"  总ROI: {basic_roi['total_roi']}%")
    print(f"  年化ROI: {basic_roi['annualized_roi']}%")
    
    # 时间价值分析
    time_value = result['time_value_analysis']
    print(f"\n💎 时间价值分析:")
    print(f"  NPV (净现值): ¥{time_value['npv']:,}")
    print(f"  IRR (内部收益率): {time_value['irr_percent']}%")
    print(f"  盈利指数: {time_value['profitability_index']}")
    print(f"  NPV评价: {time_value['npv_interpretation']}")
    print(f"  IRR评价: {time_value['irr_interpretation']}")
    
    # 回报周期
    payback = result['payback_analysis']
    print(f"\n⏱️  回报周期分析:")
    print(f"  简单回报期: {payback['simple_payback_years']}年")
    print(f"  折现回报期: {payback['discounted_payback_years']}")
    print(f"  回本速度: {payback['payback_status']}")
    
    # 多维度ROI
    multi_roi = result['multidimensional_roi']
    print(f"\n🌈 多维度ROI:")
    print(f"  财务ROI: {multi_roi['financial_roi']}%")
    print(f"  效率提升: {multi_roi['efficiency_improvement_percent']}%")
    print(f"  质量改善: {multi_roi['quality_improvement_percent']}%")
    print(f"  市场拓展: {multi_roi['market_expansion_percent']}%")
    print(f"  综合ROI: {multi_roi['comprehensive_roi']}%")
    
    # 投资建议
    recommendation = result['investment_recommendation']
    print(f"\n🎯 投资建议:")
    print(f"  建议: {recommendation['recommendation']}")
    print(f"  评级: {recommendation['level']}")
    print(f"  得分: {recommendation['score']}/100")
    print(f"  理由:")
    for reason in recommendation['reasons']:
        print(f"    - {reason}")


def example_4_key_factors():
    """示例4: 关键因素识别"""
    print_section("示例4: 关键因素识别 - 利润影响分析")
    
    # 业务数据
    business_data = {
        "revenue": 10000000,  # 营收1000万
        "costs": {
            "material": 4000000,      # 材料成本400万
            "labor": 2000000,         # 人工成本200万
            "manufacturing": 1000000, # 制造费用100万
            "sales_expense": 500000,  # 销售费用50万
            "admin_expense": 300000,  # 管理费用30万
            "financial_expense": 200000  # 财务费用20万
        },
        "profit": 2000000  # 利润200万
    }
    
    print("💼 业务概况:")
    print(f"  营收: ¥{business_data['revenue']:,}")
    print(f"  利润: ¥{business_data['profit']:,}")
    print(f"  利润率: {business_data['profit']/business_data['revenue']*100:.1f}%")
    
    # 执行分析
    result = key_factor_identifier.identify_key_factors(
        business_data=business_data,
        analysis_period="年度"
    )
    
    # 成本结构
    cost_structure = result['cost_structure']
    print(f"\n📊 成本结构:")
    print(f"  总成本: ¥{cost_structure['total_costs']:,}")
    print(f"  成本率: {cost_structure['cost_ratio']}%")
    print(f"\n  成本明细:")
    for cost_type, data in cost_structure['cost_breakdown'].items():
        print(f"    {cost_type}: ¥{data['amount']:,} ({data['percent_of_revenue']}%)")
    
    # 关键因素排名
    print(f"\n🏆 关键因素排名 (Top 5):")
    for factor in result['factor_ranking'][:5]:
        print(f"\n  {factor['rank']}. {factor['factor_name']}")
        print(f"     金额: ¥{factor.get('amount', 0):,}")
        print(f"     占营收: {factor.get('percent_of_revenue', 0)}%")
        if 'sensitivity_level' in factor:
            print(f"     敏感度: {factor['sensitivity_level']}")
        print(f"     重要性: {factor['importance_score']}")
    
    # 优化建议
    print(f"\n💡 优化建议:")
    for i, suggestion in enumerate(result['optimization_suggestions'][:3], 1):
        print(f"\n  建议{i}: {suggestion['factor']} [{suggestion['priority']}]")
        print(f"  {suggestion['suggestion']}")
        print(f"  行动方案:")
        for action in suggestion['actions']:
            print(f"    • {action}")


def example_5_long_term_prediction():
    """示例5: 长期影响预测"""
    print_section("示例5: 长期影响预测 - 新项目战略价值评估")
    
    # 项目数据
    project_data = {
        "project_id": "PRJ-2025-001",
        "estimated_order_value": 5000000,  # 预估订单额500万
        "recurrence_probability": 0.7,      # 重复购买概率70%
        "growth_rate": 0.15,                # 年增长率15%
        "market_expansion": 0.08,           # 市场扩张8%
        "competitive_factor": 0.92          # 竞争因素0.92
    }
    
    print("🚀 项目概况:")
    print(f"  项目ID: {project_data['project_id']}")
    print(f"  预估订单额: ¥{project_data['estimated_order_value']:,}")
    print(f"  重复概率: {project_data['recurrence_probability']*100}%")
    print(f"  预期增长: {project_data['growth_rate']*100}%/年")
    
    # 执行预测
    result = long_term_predictor.predict_project_impact(
        project_data=project_data,
        prediction_years=5
    )
    
    # 年度预测
    yearly = result['predictions']['yearly']
    print(f"\n📅 年度销售额预测:")
    for year, value in yearly.items():
        print(f"  {year}: ¥{value:,.2f}")
    
    # 3年影响
    three_year = result['predictions']['three_year']
    print(f"\n📊 3年累计影响:")
    print(f"  累计总额: ¥{three_year['total']:,.2f}")
    print(f"  年均值: ¥{three_year['average']:,.2f}")
    print(f"  趋势: {three_year['trend']}")
    
    # 5年影响
    five_year = result['predictions']['five_year']
    print(f"\n📈 5年累计影响:")
    print(f"  累计总额: ¥{five_year['total']:,.2f}")
    print(f"  年均值: ¥{five_year['average']:,.2f}")
    print(f"  CAGR: {five_year['cagr']}%")
    print(f"  趋势: {five_year['trend']}")
    
    # 战略影响
    strategic = result['strategic_impact']
    print(f"\n🎯 战略影响评估:")
    print(f"  3年贡献度: {strategic['three_year_contribution_percent']}%")
    print(f"  5年贡献度: {strategic['five_year_contribution_percent']}%")
    print(f"  战略重要性: {strategic['strategic_importance']}")
    print(f"  投资建议: {strategic['investment_recommendation']}")
    print(f"  风险评估: {strategic['risk_assessment']}")
    print(f"  置信度: {result['confidence_level']}")


def example_6_comprehensive_analysis():
    """示例6: 综合分析场景"""
    print_section("示例6: 综合分析 - 新产线投资决策")
    
    print("🏭 场景: 计划投资300万建设新产线")
    print("📋 需要回答的问题:")
    print("  1. 投资回报如何？")
    print("  2. 关键成功因素是什么？")
    print("  3. 长期战略价值如何？")
    print("  4. 相比行业标准如何？")
    
    # 1. ROI分析
    print("\n" + "-"*70)
    print("第1步: ROI分析")
    print("-"*70)
    
    investment_data = {
        "investment_amount": 3000000,
        "returns": [500000, 800000, 1200000, 1500000, 1800000],
        "costs": [150000, 180000, 200000, 220000, 250000],
        "time_periods": ["Year1", "Year2", "Year3", "Year4", "Year5"],
        "investment_type": "设备投资",
        "risk_level": "中"
    }
    
    roi_result = roi_deep_analyzer.analyze_roi_comprehensive(investment_data)
    print(f"  ROI: {roi_result['basic_roi']['total_roi']}%")
    print(f"  NPV: ¥{roi_result['time_value_analysis']['npv']:,.2f}")
    print(f"  IRR: {roi_result['time_value_analysis']['irr_percent']}%")
    print(f"  建议: {roi_result['investment_recommendation']['recommendation']}")
    
    # 2. 关键因素
    print("\n" + "-"*70)
    print("第2步: 识别关键成功因素")
    print("-"*70)
    
    business_data = {
        "revenue": 15000000,
        "costs": {
            "material": 6000000,
            "labor": 3000000,
            "manufacturing": 2000000,
            "sales_expense": 800000,
            "admin_expense": 500000,
            "financial_expense": 300000
        },
        "profit": 2400000
    }
    
    factors_result = key_factor_identifier.identify_key_factors(business_data)
    print("  Top 3关键因素:")
    for factor in factors_result['factor_ranking'][:3]:
        print(f"    {factor['rank']}. {factor['factor_name']} (重要性: {factor['importance_score']})")
    
    # 3. 长期预测
    print("\n" + "-"*70)
    print("第3步: 长期战略价值")
    print("-"*70)
    
    project_data = {
        "project_id": "新产线",
        "estimated_order_value": 8000000,
        "recurrence_probability": 0.8,
        "growth_rate": 0.20,
        "market_expansion": 0.10,
        "competitive_factor": 0.95
    }
    
    prediction_result = long_term_predictor.predict_project_impact(project_data)
    five_year = prediction_result['predictions']['five_year']
    print(f"  5年总影响: ¥{five_year['total']:,.2f}")
    print(f"  CAGR: {five_year['cagr']}%")
    print(f"  战略重要性: {prediction_result['strategic_impact']['strategic_importance']}")
    
    # 4. 行业对比
    print("\n" + "-"*70)
    print("第4步: 行业对比")
    print("-"*70)
    
    company_data = {
        "revenue_growth": 0.20,
        "profit_margin": 0.16,
        "roe": 0.22
    }
    
    industry_result = industry_comparator.compare_with_industry(
        company_data, 
        "制造业"
    )
    print(f"  行业评估: {industry_result['overall_assessment']}")
    print(f"  综合得分: {industry_result['average_score']}/4.0")
    
    # 综合结论
    print("\n" + "="*70)
    print("🎯 综合决策建议")
    print("="*70)
    print(f"""
  ✅ ROI分析: {roi_result['investment_recommendation']['recommendation']}
  ✅ 回报周期: {roi_result['payback_analysis']['simple_payback_years']}年
  ✅ 战略价值: {prediction_result['strategic_impact']['strategic_importance']}
  ✅ 行业地位: {industry_result['overall_assessment']}
  
  💡 建议: 该投资项目具有良好的财务回报和战略价值，建议推进！
    """)


def main():
    """主函数 - 运行所有示例"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "高级经营分析模块 - 使用示例" + " "*15 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        # 运行所有示例
        example_1_industry_comparison()
        example_2_competitive_position()
        example_3_roi_analysis()
        example_4_key_factors()
        example_5_long_term_prediction()
        example_6_comprehensive_analysis()
        
        print("\n" + "="*70)
        print("✅ 所有示例运行完成！")
        print("="*70)
        print("\n💡 提示: 您可以修改示例数据来测试不同场景")
        print("📚 详细文档请参考: README.md")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

