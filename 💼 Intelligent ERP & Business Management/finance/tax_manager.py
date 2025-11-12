"""
ERP系统 - 税务管理模块
支持税率配置、自动计税、税务报表、发票管理
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaxType(str, Enum):
    """税种类型"""
    VAT = "vat"  # 增值税
    INCOME = "income"  # 所得税
    SALES = "sales"  # 销售税
    IMPORT = "import"  # 进口关税
    EXCISE = "excise"  # 消费税
    STAMP = "stamp"  # 印花税


class TaxRate(BaseModel):
    """税率模型"""
    id: Optional[int] = None
    tax_type: TaxType  # 税种类型
    name: str  # 税率名称
    rate: Decimal  # 税率（百分比）
    description: str = ""  # 描述
    applicable_from: date  # 生效日期
    applicable_to: Optional[date] = None  # 失效日期
    is_active: bool = True


class TaxCalculation(BaseModel):
    """税额计算结果"""
    amount: Decimal  # 原始金额
    tax_type: TaxType  # 税种
    tax_rate: Decimal  # 税率
    tax_amount: Decimal  # 税额
    total_amount: Decimal  # 含税总额
    calculation_date: datetime = datetime.now()


class Invoice(BaseModel):
    """发票模型"""
    id: Optional[int] = None
    invoice_number: str  # 发票号码
    invoice_type: str  # 发票类型（增值税专用/普通）
    issue_date: date  # 开票日期
    seller_name: str  # 销售方名称
    seller_tax_id: str  # 销售方税号
    buyer_name: str  # 购买方名称
    buyer_tax_id: str  # 购买方税号
    amount: Decimal  # 金额
    tax_amount: Decimal  # 税额
    total_amount: Decimal  # 价税合计
    status: str = "draft"  # 状态（draft/issued/cancelled）


class TaxManager:
    """
    税务管理器
    
    功能：
    - 税率配置和管理
    - 自动计税
    - 发票管理
    - 税务报表生成
    """
    
    def __init__(self):
        """初始化税务管理器"""
        self.tax_rates: List[TaxRate] = []
        self.invoices: List[Invoice] = []
        self._init_default_tax_rates()
    
    def _init_default_tax_rates(self):
        """初始化默认税率"""
        # 中国增值税率
        default_rates = [
            TaxRate(
                id=1,
                tax_type=TaxType.VAT,
                name="增值税-13%",
                rate=Decimal("13.0"),
                description="一般纳税人标准税率",
                applicable_from=date(2019, 4, 1)
            ),
            TaxRate(
                id=2,
                tax_type=TaxType.VAT,
                name="增值税-9%",
                rate=Decimal("9.0"),
                description="交通运输、邮政等",
                applicable_from=date(2019, 4, 1)
            ),
            TaxRate(
                id=3,
                tax_type=TaxType.VAT,
                name="增值税-6%",
                rate=Decimal("6.0"),
                description="现代服务业等",
                applicable_from=date(2019, 4, 1)
            ),
            TaxRate(
                id=4,
                tax_type=TaxType.VAT,
                name="增值税-3%",
                rate=Decimal("3.0"),
                description="小规模纳税人",
                applicable_from=date(2019, 4, 1)
            ),
            TaxRate(
                id=5,
                tax_type=TaxType.INCOME,
                name="企业所得税-25%",
                rate=Decimal("25.0"),
                description="企业所得税标准税率",
                applicable_from=date(2008, 1, 1)
            ),
        ]
        
        self.tax_rates.extend(default_rates)
    
    def add_tax_rate(self, tax_rate: TaxRate) -> bool:
        """
        添加税率
        
        Args:
            tax_rate: 税率对象
            
        Returns:
            是否添加成功
        """
        try:
            if tax_rate.id is None:
                tax_rate.id = len(self.tax_rates) + 1
            
            self.tax_rates.append(tax_rate)
            logger.info(f"添加税率: {tax_rate.name} - {tax_rate.rate}%")
            return True
            
        except Exception as e:
            logger.error(f"添加税率失败: {e}")
            return False
    
    def get_tax_rate(
        self,
        tax_type: TaxType,
        calculation_date: Optional[date] = None
    ) -> Optional[TaxRate]:
        """
        获取税率
        
        Args:
            tax_type: 税种类型
            calculation_date: 计算日期
            
        Returns:
            税率对象
        """
        if calculation_date is None:
            calculation_date = datetime.now().date()
        
        # 查找符合条件的税率
        applicable_rates = [
            rate for rate in self.tax_rates
            if rate.tax_type == tax_type
            and rate.is_active
            and rate.applicable_from <= calculation_date
            and (rate.applicable_to is None or rate.applicable_to >= calculation_date)
        ]
        
        # 返回第一个匹配的税率（或最新的）
        if applicable_rates:
            return applicable_rates[0]
        
        return None
    
    def calculate_tax(
        self,
        amount: Decimal,
        tax_type: TaxType,
        is_tax_included: bool = False,
        calculation_date: Optional[date] = None
    ) -> Optional[TaxCalculation]:
        """
        计算税额
        
        Args:
            amount: 金额
            tax_type: 税种类型
            is_tax_included: 是否含税
            calculation_date: 计算日期
            
        Returns:
            税额计算结果
        """
        # 获取税率
        tax_rate = self.get_tax_rate(tax_type, calculation_date)
        if not tax_rate:
            logger.error(f"未找到适用的税率: {tax_type}")
            return None
        
        rate = tax_rate.rate / Decimal("100")  # 转换为小数
        
        if is_tax_included:
            # 含税金额，需要先分离出不含税金额
            tax_free_amount = amount / (Decimal("1") + rate)
            tax_amount = amount - tax_free_amount
            total_amount = amount
        else:
            # 不含税金额
            tax_free_amount = amount
            tax_amount = amount * rate
            total_amount = amount + tax_amount
        
        result = TaxCalculation(
            amount=tax_free_amount,
            tax_type=tax_type,
            tax_rate=tax_rate.rate,
            tax_amount=tax_amount,
            total_amount=total_amount
        )
        
        logger.info(
            f"计税: {amount} × {tax_rate.rate}% = {tax_amount}"
        )
        
        return result
    
    def create_invoice(
        self,
        invoice_number: str,
        seller_name: str,
        seller_tax_id: str,
        buyer_name: str,
        buyer_tax_id: str,
        amount: Decimal,
        tax_calculation: TaxCalculation
    ) -> Invoice:
        """
        创建发票
        
        Args:
            invoice_number: 发票号码
            seller_name: 销售方
            seller_tax_id: 销售方税号
            buyer_name: 购买方
            buyer_tax_id: 购买方税号
            amount: 金额
            tax_calculation: 税额计算结果
            
        Returns:
            发票对象
        """
        invoice = Invoice(
            id=len(self.invoices) + 1,
            invoice_number=invoice_number,
            invoice_type="增值税专用发票",
            issue_date=datetime.now().date(),
            seller_name=seller_name,
            seller_tax_id=seller_tax_id,
            buyer_name=buyer_name,
            buyer_tax_id=buyer_tax_id,
            amount=tax_calculation.amount,
            tax_amount=tax_calculation.tax_amount,
            total_amount=tax_calculation.total_amount,
            status="issued"
        )
        
        self.invoices.append(invoice)
        logger.info(f"创建发票: {invoice_number}")
        
        return invoice
    
    def get_tax_report(
        self,
        start_date: date,
        end_date: date,
        tax_type: Optional[TaxType] = None
    ) -> Dict[str, any]:
        """
        生成税务报表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            tax_type: 税种类型（可选）
            
        Returns:
            税务报表数据
        """
        # 筛选发票
        filtered_invoices = [
            inv for inv in self.invoices
            if start_date <= inv.issue_date <= end_date
            and inv.status == "issued"
        ]
        
        # 统计
        total_amount = sum(inv.amount for inv in filtered_invoices)
        total_tax = sum(inv.tax_amount for inv in filtered_invoices)
        invoice_count = len(filtered_invoices)
        
        report = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "invoice_count": invoice_count,
                "total_amount": float(total_amount),
                "total_tax": float(total_tax),
                "total_with_tax": float(total_amount + total_tax)
            },
            "invoices": [
                {
                    "invoice_number": inv.invoice_number,
                    "buyer": inv.buyer_name,
                    "amount": float(inv.amount),
                    "tax": float(inv.tax_amount),
                    "issue_date": inv.issue_date.isoformat()
                }
                for inv in filtered_invoices
            ]
        }
        
        logger.info(f"生成税务报表: {start_date} - {end_date}")
        return report


# 全局实例
_tax_manager: Optional[TaxManager] = None


def get_tax_manager() -> TaxManager:
    """获取全局税务管理器实例"""
    global _tax_manager
    if _tax_manager is None:
        _tax_manager = TaxManager()
    return _tax_manager


# 使用示例
def example_usage():
    """使用示例"""
    
    manager = get_tax_manager()
    
    # 1. 计算增值税
    tax_calc = manager.calculate_tax(
        amount=Decimal("10000"),
        tax_type=TaxType.VAT,
        is_tax_included=False
    )
    
    print(f"金额: {tax_calc.amount}")
    print(f"税率: {tax_calc.tax_rate}%")
    print(f"税额: {tax_calc.tax_amount}")
    print(f"价税合计: {tax_calc.total_amount}")
    
    # 2. 创建发票
    invoice = manager.create_invoice(
        invoice_number="INV20251107001",
        seller_name="ABC公司",
        seller_tax_id="123456789",
        buyer_name="XYZ公司",
        buyer_tax_id="987654321",
        amount=Decimal("10000"),
        tax_calculation=tax_calc
    )
    
    print(f"发票创建成功: {invoice.invoice_number}")
    
    # 3. 生成税务报表
    report = manager.get_tax_report(
        start_date=date(2025, 11, 1),
        end_date=date(2025, 11, 30)
    )
    
    print(f"发票数量: {report['summary']['invoice_count']}")
    print(f"总税额: {report['summary']['total_tax']}")


if __name__ == "__main__":
    example_usage()


















