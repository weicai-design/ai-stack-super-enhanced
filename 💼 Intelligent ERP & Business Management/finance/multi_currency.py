"""
ERP系统 - 多币种支持模块
支持多币种交易、汇率管理、货币转换
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal
import requests
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Currency(BaseModel):
    """货币模型"""
    code: str  # 货币代码（如 CNY, USD, EUR）
    name: str  # 货币名称
    symbol: str  # 货币符号（如 ¥, $, €）
    decimal_places: int = 2  # 小数位数
    is_active: bool = True


class ExchangeRate(BaseModel):
    """汇率模型"""
    from_currency: str  # 源货币
    to_currency: str  # 目标货币
    rate: Decimal  # 汇率
    date: date  # 汇率日期
    source: str = "manual"  # 汇率来源（manual/api/bank）


class MultiCurrencyManager:
    """
    多币种管理器
    
    功能：
    - 币种管理
    - 汇率管理
    - 货币转换
    - 多币种报表
    """
    
    def __init__(self, base_currency: str = "CNY"):
        """
        初始化多币种管理器
        
        Args:
            base_currency: 基础货币（默认人民币）
        """
        self.base_currency = base_currency
        self.currencies = self._init_currencies()
        self.exchange_rates = {}
    
    def _init_currencies(self) -> Dict[str, Currency]:
        """初始化支持的货币"""
        currencies = {
            "CNY": Currency(
                code="CNY",
                name="人民币",
                symbol="¥",
                decimal_places=2
            ),
            "USD": Currency(
                code="USD",
                name="美元",
                symbol="$",
                decimal_places=2
            ),
            "EUR": Currency(
                code="EUR",
                name="欧元",
                symbol="€",
                decimal_places=2
            ),
            "GBP": Currency(
                code="GBP",
                name="英镑",
                symbol="£",
                decimal_places=2
            ),
            "JPY": Currency(
                code="JPY",
                name="日元",
                symbol="¥",
                decimal_places=0
            ),
            "HKD": Currency(
                code="HKD",
                name="港币",
                symbol="HK$",
                decimal_places=2
            ),
            "KRW": Currency(
                code="KRW",
                name="韩元",
                symbol="₩",
                decimal_places=0
            ),
        }
        return currencies
    
    def add_currency(self, currency: Currency) -> bool:
        """
        添加支持的货币
        
        Args:
            currency: 货币对象
            
        Returns:
            是否添加成功
        """
        try:
            self.currencies[currency.code] = currency
            logger.info(f"添加货币: {currency.code} - {currency.name}")
            return True
        except Exception as e:
            logger.error(f"添加货币失败: {e}")
            return False
    
    def get_currency(self, code: str) -> Optional[Currency]:
        """
        获取货币信息
        
        Args:
            code: 货币代码
            
        Returns:
            货币对象
        """
        return self.currencies.get(code)
    
    def list_currencies(self, active_only: bool = True) -> List[Currency]:
        """
        列出所有货币
        
        Args:
            active_only: 是否只返回激活的货币
            
        Returns:
            货币列表
        """
        currencies = list(self.currencies.values())
        if active_only:
            currencies = [c for c in currencies if c.is_active]
        return currencies
    
    def set_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        date: Optional[date] = None,
        source: str = "manual"
    ) -> bool:
        """
        设置汇率
        
        Args:
            from_currency: 源货币
            to_currency: 目标货币
            rate: 汇率
            date: 汇率日期
            source: 汇率来源
            
        Returns:
            是否设置成功
        """
        try:
            if date is None:
                date = datetime.now().date()
            
            key = f"{from_currency}_{to_currency}_{date}"
            
            exchange_rate = ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                date=date,
                source=source
            )
            
            self.exchange_rates[key] = exchange_rate
            logger.info(f"设置汇率: {from_currency}/{to_currency} = {rate}")
            return True
            
        except Exception as e:
            logger.error(f"设置汇率失败: {e}")
            return False
    
    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        获取汇率
        
        Args:
            from_currency: 源货币
            to_currency: 目标货币
            date: 汇率日期
            
        Returns:
            汇率，不存在则返回None
        """
        # 如果是同一货币，汇率为1
        if from_currency == to_currency:
            return Decimal("1.0")
        
        if date is None:
            date = datetime.now().date()
        
        key = f"{from_currency}_{to_currency}_{date}"
        
        if key in self.exchange_rates:
            return self.exchange_rates[key].rate
        
        # 尝试从API获取
        return self._fetch_exchange_rate_from_api(from_currency, to_currency)
    
    def _fetch_exchange_rate_from_api(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[Decimal]:
        """
        从API获取实时汇率
        
        使用免费的汇率API（示例）
        实际可替换为央行API或商业API
        """
        try:
            # 使用exchangerate-api.com（免费）
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rate = Decimal(str(data["rates"][to_currency]))
                
                # 保存汇率
                self.set_exchange_rate(
                    from_currency,
                    to_currency,
                    rate,
                    source="api"
                )
                
                logger.info(f"从API获取汇率: {from_currency}/{to_currency} = {rate}")
                return rate
            
        except Exception as e:
            logger.error(f"获取API汇率失败: {e}")
        
        return None
    
    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        date: Optional[date] = None
    ) -> Optional[Decimal]:
        """
        货币转换
        
        Args:
            amount: 金额
            from_currency: 源货币
            to_currency: 目标货币
            date: 汇率日期
            
        Returns:
            转换后的金额
        """
        rate = self.get_exchange_rate(from_currency, to_currency, date)
        
        if rate is None:
            logger.error(f"无法获取汇率: {from_currency} → {to_currency}")
            return None
        
        converted = amount * rate
        
        # 根据目标货币的小数位数进行四舍五入
        target_currency = self.get_currency(to_currency)
        if target_currency:
            decimal_places = target_currency.decimal_places
            converted = round(converted, decimal_places)
        
        logger.debug(f"货币转换: {amount} {from_currency} = {converted} {to_currency}")
        return converted
    
    def format_amount(self, amount: Decimal, currency: str) -> str:
        """
        格式化金额显示
        
        Args:
            amount: 金额
            currency: 货币代码
            
        Returns:
            格式化的金额字符串
        """
        curr = self.get_currency(currency)
        if not curr:
            return f"{amount} {currency}"
        
        # 格式化数字
        formatted = f"{amount:,.{curr.decimal_places}f}"
        
        # 添加货币符号
        return f"{curr.symbol}{formatted}"
    
    def get_multi_currency_total(
        self,
        amounts: List[Dict[str, any]],
        target_currency: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        计算多币种总额
        
        Args:
            amounts: 金额列表 [{"amount": 100, "currency": "USD"}, ...]
            target_currency: 目标货币（如果指定则转换）
            
        Returns:
            各币种总额或转换后总额
        """
        if target_currency:
            # 转换为目标货币
            total = Decimal("0")
            for item in amounts:
                amount = Decimal(str(item["amount"]))
                from_curr = item["currency"]
                
                converted = self.convert(amount, from_curr, target_currency)
                if converted:
                    total += converted
            
            return {target_currency: total}
        else:
            # 按币种分组汇总
            totals = {}
            for item in amounts:
                currency = item["currency"]
                amount = Decimal(str(item["amount"]))
                
                if currency in totals:
                    totals[currency] += amount
                else:
                    totals[currency] = amount
            
            return totals
    
    def update_all_rates_from_api(self):
        """
        从API更新所有汇率
        
        批量更新所有货币对的汇率
        """
        logger.info("开始批量更新汇率...")
        
        updated_count = 0
        for from_curr in self.currencies.keys():
            for to_curr in self.currencies.keys():
                if from_curr != to_curr:
                    rate = self._fetch_exchange_rate_from_api(from_curr, to_curr)
                    if rate:
                        updated_count += 1
        
        logger.info(f"汇率更新完成: 更新{updated_count}个汇率")
        return updated_count


# 全局实例
_multi_currency_manager: Optional[MultiCurrencyManager] = None


def get_currency_manager() -> MultiCurrencyManager:
    """获取全局多币种管理器实例"""
    global _multi_currency_manager
    if _multi_currency_manager is None:
        _multi_currency_manager = MultiCurrencyManager()
    return _multi_currency_manager


# 使用示例
def example_usage():
    """使用示例"""
    
    manager = get_currency_manager()
    
    # 1. 列出支持的货币
    currencies = manager.list_currencies()
    print(f"支持的货币: {len(currencies)}种")
    
    # 2. 设置汇率
    manager.set_exchange_rate("USD", "CNY", Decimal("7.2"))
    
    # 3. 货币转换
    amount_usd = Decimal("100")
    amount_cny = manager.convert(amount_usd, "USD", "CNY")
    print(f"$100 = ¥{amount_cny}")
    
    # 4. 格式化显示
    formatted = manager.format_amount(amount_cny, "CNY")
    print(f"格式化: {formatted}")
    
    # 5. 多币种总额计算
    amounts = [
        {"amount": 100, "currency": "USD"},
        {"amount": 500, "currency": "CNY"},
        {"amount": 80, "currency": "EUR"}
    ]
    
    # 转换为人民币总额
    total = manager.get_multi_currency_total(amounts, target_currency="CNY")
    print(f"人民币总额: ¥{total['CNY']}")


if __name__ == "__main__":
    example_usage()


















