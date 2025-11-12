"""
ERP系统 - 供应商评分系统
基于多维度的供应商综合评分
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class SupplierScoreCard(BaseModel):
    """供应商评分卡"""
    supplier_id: int
    supplier_name: str
    evaluation_date: date
    
    # 评分维度（0-100分）
    quality_score: Decimal  # 质量评分
    delivery_score: Decimal  # 交付评分
    price_score: Decimal  # 价格评分
    service_score: Decimal  # 服务评分
    compliance_score: Decimal  # 合规评分
    
    # 综合评分
    total_score: Decimal
    grade: str  # 评级（A/B/C/D）
    
    # 权重配置
    weights: Dict[str, Decimal] = {
        "quality": Decimal("0.3"),
        "delivery": Decimal("0.25"),
        "price": Decimal("0.20"),
        "service": Decimal("0.15"),
        "compliance": Decimal("0.10")
    }


class SupplierPerformance(BaseModel):
    """供应商绩效数据"""
    supplier_id: int
    period_start: date
    period_end: date
    
    # 质量指标
    total_orders: int  # 总订单数
    defect_orders: int  # 有缺陷订单数
    defect_rate: Decimal  # 缺陷率
    
    # 交付指标
    on_time_deliveries: int  # 准时交付数
    on_time_rate: Decimal  # 准时率
    avg_delay_days: Decimal  # 平均延误天数
    
    # 价格指标
    price_variance: Decimal  # 价格偏差率
    payment_terms: int  # 付款账期（天）
    
    # 服务指标
    response_time_hours: Decimal  # 响应时间（小时）
    issue_resolution_rate: Decimal  # 问题解决率


class SupplierScoringSystem:
    """
    供应商评分系统
    
    功能：
    - 多维度评分
    - 自动评分计算
    - 评级分类
    - 评分趋势分析
    """
    
    def __init__(self):
        """初始化评分系统"""
        self.score_cards: List[SupplierScoreCard] = []
        self.performance_data: List[SupplierPerformance] = []
    
    def calculate_quality_score(self, performance: SupplierPerformance) -> Decimal:
        """
        计算质量评分
        
        基于缺陷率：
        - 0-2%: 95-100分
        - 2-5%: 85-95分
        - 5-10%: 70-85分
        - >10%: <70分
        """
        defect_rate = performance.defect_rate
        
        if defect_rate <= Decimal("2"):
            score = Decimal("100") - defect_rate * Decimal("2.5")
        elif defect_rate <= Decimal("5"):
            score = Decimal("95") - (defect_rate - Decimal("2")) * Decimal("3.33")
        elif defect_rate <= Decimal("10"):
            score = Decimal("85") - (defect_rate - Decimal("5")) * Decimal("3")
        else:
            score = Decimal("70") - (defect_rate - Decimal("10")) * Decimal("2")
        
        return max(Decimal("0"), min(Decimal("100"), score))
    
    def calculate_delivery_score(self, performance: SupplierPerformance) -> Decimal:
        """
        计算交付评分
        
        基于准时率和延误天数
        """
        on_time_rate = performance.on_time_rate
        delay_penalty = performance.avg_delay_days * Decimal("2")
        
        score = on_time_rate - delay_penalty
        return max(Decimal("0"), min(Decimal("100"), score))
    
    def calculate_price_score(self, performance: SupplierPerformance) -> Decimal:
        """
        计算价格评分
        
        基于价格偏差率
        """
        variance = abs(performance.price_variance)
        
        if variance <= Decimal("5"):
            score = Decimal("100") - variance * Decimal("2")
        elif variance <= Decimal("10"):
            score = Decimal("90") - (variance - Decimal("5")) * Decimal("4")
        else:
            score = Decimal("70") - (variance - Decimal("10")) * Decimal("2")
        
        return max(Decimal("0"), min(Decimal("100"), score))
    
    def calculate_service_score(self, performance: SupplierPerformance) -> Decimal:
        """
        计算服务评分
        
        基于响应时间和问题解决率
        """
        # 响应时间评分（24小时内响应为满分）
        response_score = max(
            Decimal("0"),
            Decimal("100") - performance.response_time_hours * Decimal("2")
        )
        
        # 问题解决率评分
        resolution_score = performance.issue_resolution_rate
        
        # 综合评分
        score = response_score * Decimal("0.4") + resolution_score * Decimal("0.6")
        
        return max(Decimal("0"), min(Decimal("100"), score))
    
    def calculate_compliance_score(self, supplier_id: int) -> Decimal:
        """
        计算合规评分
        
        基于资质、证书、合同履行情况等
        """
        # TODO: 实际应该从合规记录中计算
        # 这里返回默认值
        return Decimal("90")
    
    def evaluate_supplier(
        self,
        supplier_id: int,
        supplier_name: str,
        performance: SupplierPerformance
    ) -> SupplierScoreCard:
        """
        评估供应商
        
        Args:
            supplier_id: 供应商ID
            supplier_name: 供应商名称
            performance: 绩效数据
            
        Returns:
            评分卡
        """
        # 计算各维度评分
        quality_score = self.calculate_quality_score(performance)
        delivery_score = self.calculate_delivery_score(performance)
        price_score = self.calculate_price_score(performance)
        service_score = self.calculate_service_score(performance)
        compliance_score = self.calculate_compliance_score(supplier_id)
        
        # 创建评分卡
        score_card = SupplierScoreCard(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            evaluation_date=datetime.now().date(),
            quality_score=quality_score,
            delivery_score=delivery_score,
            price_score=price_score,
            service_score=service_score,
            compliance_score=compliance_score,
            total_score=Decimal("0")  # 将在下面计算
        )
        
        # 计算加权总分
        total_score = (
            quality_score * score_card.weights["quality"] +
            delivery_score * score_card.weights["delivery"] +
            price_score * score_card.weights["price"] +
            service_score * score_card.weights["service"] +
            compliance_score * score_card.weights["compliance"]
        )
        
        score_card.total_score = round(total_score, 2)
        
        # 确定评级
        if total_score >= 90:
            score_card.grade = "A"
        elif total_score >= 80:
            score_card.grade = "B"
        elif total_score >= 70:
            score_card.grade = "C"
        else:
            score_card.grade = "D"
        
        self.score_cards.append(score_card)
        
        logger.info(
            f"供应商评分完成: {supplier_name} - {score_card.grade}级 ({total_score}分)"
        )
        
        return score_card
    
    def get_supplier_rank(self, top_n: int = 10) -> List[SupplierScoreCard]:
        """
        获取供应商排名
        
        Args:
            top_n: 返回前N名
            
        Returns:
            排名列表
        """
        # 按总分降序排序
        sorted_cards = sorted(
            self.score_cards,
            key=lambda x: x.total_score,
            reverse=True
        )
        
        return sorted_cards[:top_n]
    
    def get_suppliers_by_grade(self, grade: str) -> List[SupplierScoreCard]:
        """
        按评级筛选供应商
        
        Args:
            grade: 评级（A/B/C/D）
            
        Returns:
            供应商列表
        """
        return [card for card in self.score_cards if card.grade == grade]
    
    def generate_evaluation_report(
        self,
        supplier_id: Optional[int] = None
    ) -> Dict[str, any]:
        """
        生成评估报告
        
        Args:
            supplier_id: 供应商ID（可选，不指定则生成全部）
            
        Returns:
            评估报告
        """
        cards = self.score_cards
        
        if supplier_id:
            cards = [c for c in cards if c.supplier_id == supplier_id]
        
        if not cards:
            return {"error": "无评估数据"}
        
        # 统计
        avg_score = sum(c.total_score for c in cards) / len(cards)
        
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
        for card in cards:
            if card.grade in grade_counts:
                grade_counts[card.grade] += 1
        
        report = {
            "summary": {
                "total_suppliers": len(cards),
                "average_score": float(avg_score),
                "grade_distribution": grade_counts
            },
            "top_suppliers": [
                {
                    "name": card.supplier_name,
                    "score": float(card.total_score),
                    "grade": card.grade
                }
                for card in self.get_supplier_rank(5)
            ],
            "by_grade": {
                grade: len(self.get_suppliers_by_grade(grade))
                for grade in ["A", "B", "C", "D"]
            }
        }
        
        return report


# 全局实例
_scoring_system: Optional[SupplierScoringSystem] = None


def get_scoring_system() -> SupplierScoringSystem:
    """获取全局评分系统实例"""
    global _scoring_system
    if _scoring_system is None:
        _scoring_system = SupplierScoringSystem()
    return _scoring_system


# 使用示例
def example_usage():
    """使用示例"""
    
    system = get_scoring_system()
    
    # 1. 准备绩效数据
    performance = SupplierPerformance(
        supplier_id=1,
        period_start=date(2025, 1, 1),
        period_end=date(2025, 10, 31),
        total_orders=100,
        defect_orders=3,
        defect_rate=Decimal("3.0"),
        on_time_deliveries=92,
        on_time_rate=Decimal("92"),
        avg_delay_days=Decimal("1.5"),
        price_variance=Decimal("3.5"),
        payment_terms=30,
        response_time_hours=Decimal("4"),
        issue_resolution_rate=Decimal("95")
    )
    
    # 2. 评估供应商
    score_card = system.evaluate_supplier(
        supplier_id=1,
        supplier_name="优质供应商A",
        performance=performance
    )
    
    print(f"供应商: {score_card.supplier_name}")
    print(f"质量评分: {score_card.quality_score}")
    print(f"交付评分: {score_card.delivery_score}")
    print(f"价格评分: {score_card.price_score}")
    print(f"服务评分: {score_card.service_score}")
    print(f"总分: {score_card.total_score}")
    print(f"评级: {score_card.grade}")
    
    # 3. 查看排名
    top_suppliers = system.get_supplier_rank(5)
    print(f"\n前5名供应商:")
    for i, card in enumerate(top_suppliers, 1):
        print(f"{i}. {card.supplier_name} - {card.grade}级 ({card.total_score}分)")
    
    # 4. 生成评估报表
    report = system.generate_evaluation_report()
    print(f"\n评估报表: {report}")


if __name__ == "__main__":
    example_usage()


















