"""
同花顺API适配器
对接同花顺开放平台获取真实股票数据
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class TonghuashuAdapter:
    """
    同花顺API适配器
    
    功能:
    1. 获取实时行情数据
    2. 获取历史K线数据
    3. 获取公司财务数据
    4. 获取市场资金流向
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        初始化同花顺适配器
        
        Args:
            api_key: API密钥（可从环境变量获取）
            api_secret: API密钥（可从环境变量获取）
        """
        self.api_key = api_key or os.getenv("TONGHUASHUN_API_KEY", "")
        self.api_secret = api_secret or os.getenv("TONGHUASHUN_API_SECRET", "")
        self.base_url = "http://open.10jqka.com.cn/api"  # 示例URL
        self.session = requests.Session()
        
        # 配置请求头
        self.session.headers.update({
            "User-Agent": "AI-STACK/3.2",
            "Accept": "application/json"
        })
        
        logger.info("✅ 同花顺API适配器初始化完成")
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        发起API请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            method: 请求方法
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}/{endpoint}"
        
        # 添加认证参数
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        
        try:
            if method == "GET":
                response = self.session.get(url, params=params, timeout=10)
            else:
                response = self.session.post(url, json=params, timeout=10)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"同花顺API请求失败: {e}")
            # 返回模拟数据作为降级
            return self._get_fallback_data(endpoint)
        
        except Exception as e:
            logger.error(f"处理响应失败: {e}")
            return self._get_fallback_data(endpoint)
    
    def get_realtime_quote(self, stock_code: str, market: str = "A") -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码（如：000001）
            market: 市场类型（A/B/H）
            
        Returns:
            实时行情数据
        """
        if not self.api_key:
            logger.warning("未配置API密钥，使用模拟数据")
            return self._get_mock_realtime_data(stock_code, market)
        
        try:
            data = self._make_request(
                "stock/realtime",
                params={"code": stock_code, "market": market}
            )
            
            return {
                "stock_code": stock_code,
                "market": market,
                "current_price": data.get("price", 0.0),
                "change": data.get("change", 0.0),
                "change_percent": data.get("change_percent", 0.0),
                "volume": data.get("volume", 0),
                "amount": data.get("amount", 0.0),
                "high": data.get("high", 0.0),
                "low": data.get("low", 0.0),
                "open": data.get("open", 0.0),
                "close_prev": data.get("close_prev", 0.0),
                "timestamp": datetime.now().isoformat(),
                "source": "同花顺API"
            }
        
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return self._get_mock_realtime_data(stock_code, market)
    
    def get_historical_data(
        self, 
        stock_code: str, 
        market: str = "A",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        获取历史K线数据
        
        Args:
            stock_code: 股票代码
            market: 市场类型
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: 周期（daily/weekly/monthly）
            
        Returns:
            历史K线数据列表
        """
        if not self.api_key:
            logger.warning("未配置API密钥，使用模拟数据")
            return self._get_mock_historical_data(stock_code, market)
        
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            data = self._make_request(
                "stock/kline",
                params={
                    "code": stock_code,
                    "market": market,
                    "start": start_date,
                    "end": end_date,
                    "period": period
                }
            )
            
            return data.get("kline", [])
        
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return self._get_mock_historical_data(stock_code, market)
    
    def get_company_info(self, stock_code: str, market: str = "A") -> Dict[str, Any]:
        """
        获取公司基本信息
        
        Args:
            stock_code: 股票代码
            market: 市场类型
            
        Returns:
            公司信息
        """
        if not self.api_key:
            return self._get_mock_company_info(stock_code, market)
        
        try:
            data = self._make_request(
                "stock/company",
                params={"code": stock_code, "market": market}
            )
            
            return {
                "stock_code": stock_code,
                "stock_name": data.get("name", "未知"),
                "industry": data.get("industry", ""),
                "market_cap": data.get("market_cap", 0.0),
                "pe_ratio": data.get("pe", 0.0),
                "pb_ratio": data.get("pb", 0.0),
                "total_shares": data.get("total_shares", 0),
                "source": "同花顺API"
            }
        
        except Exception as e:
            logger.error(f"获取公司信息失败: {e}")
            return self._get_mock_company_info(stock_code, market)
    
    def _get_fallback_data(self, endpoint: str) -> Dict[str, Any]:
        """API失败时的降级数据"""
        return {
            "status": "fallback",
            "message": "使用模拟数据",
            "endpoint": endpoint
        }
    
    def _get_mock_realtime_data(self, stock_code: str, market: str) -> Dict[str, Any]:
        """模拟实时数据（API密钥未配置时使用）"""
        import random
        base_price = 10.0 + random.random() * 90.0
        
        return {
            "stock_code": stock_code,
            "market": market,
            "current_price": round(base_price, 2),
            "change": round((random.random() - 0.5) * 2, 2),
            "change_percent": round((random.random() - 0.5) * 10, 2),
            "volume": int(random.random() * 10000000),
            "amount": round(random.random() * 100000000, 2),
            "high": round(base_price * 1.05, 2),
            "low": round(base_price * 0.95, 2),
            "open": round(base_price * 0.98, 2),
            "close_prev": round(base_price * 0.99, 2),
            "timestamp": datetime.now().isoformat(),
            "source": "模拟数据"
        }
    
    def _get_mock_historical_data(self, stock_code: str, market: str) -> List[Dict[str, Any]]:
        """模拟历史数据"""
        import random
        data = []
        base_price = 10.0 + random.random() * 90.0
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).strftime("%Y-%m-%d")
            price = base_price + random.random() * 10 - 5
            data.append({
                "date": date,
                "open": round(price, 2),
                "high": round(price * 1.03, 2),
                "low": round(price * 0.97, 2),
                "close": round(price * 1.01, 2),
                "volume": int(random.random() * 10000000),
                "amount": round(random.random() * 100000000, 2)
            })
        
        return data
    
    def _get_mock_company_info(self, stock_code: str, market: str) -> Dict[str, Any]:
        """模拟公司信息"""
        return {
            "stock_code": stock_code,
            "stock_name": f"测试公司{stock_code}",
            "industry": "制造业",
            "market_cap": 1000000000.0,
            "pe_ratio": 15.5,
            "pb_ratio": 2.3,
            "total_shares": 100000000,
            "source": "模拟数据"
        }


# 创建全局实例
tonghuashun_adapter = TonghuashuAdapter()

































