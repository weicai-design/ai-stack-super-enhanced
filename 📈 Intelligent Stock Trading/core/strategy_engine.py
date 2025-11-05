"""
Stock Strategy Engine
股票策略引擎

根据需求3.2: 制定顶级投资策略
根据需求3.5: 不断优化投资策略
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics


class StrategyEngine:
    """策略引擎基类"""
    
    def __init__(self, name: str, description: str):
        """
        初始化策略引擎
        
        Args:
            name: 策略名称
            description: 策略描述
        """
        self.name = name
        self.description = description
        self.performance_history = []
    
    def analyze(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析股票数据
        
        Args:
            stock_data: 股票数据
            
        Returns:
            分析结果
        """
        raise NotImplementedError("子类需要实现analyze方法")
    
    def generate_signal(self, analysis: Dict[str, Any]) -> str:
        """
        生成交易信号
        
        Args:
            analysis: 分析结果
            
        Returns:
            交易信号 (buy/sell/hold)
        """
        raise NotImplementedError("子类需要实现generate_signal方法")
    
    def record_performance(self, result: Dict[str, Any]):
        """
        记录策略表现
        
        根据需求3.5: 根据买卖结果优化策略
        
        Args:
            result: 交易结果
        """
        self.performance_history.append({
            "timestamp": datetime.now().isoformat(),
            "result": result,
        })
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取策略表现指标
        
        根据需求3.5: 提供收益概率、收益率
        
        Returns:
            表现指标
        """
        if not self.performance_history:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_return": 0,
                "avg_return": 0,
            }
        
        total_trades = len(self.performance_history)
        wins = sum(1 for h in self.performance_history if h["result"].get("profit", 0) > 0)
        win_rate = wins / total_trades * 100 if total_trades > 0 else 0
        
        total_return = sum(h["result"].get("return_rate", 0) for h in self.performance_history)
        avg_return = total_return / total_trades if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_return": round(total_return, 2),
            "avg_return": round(avg_return, 2),
        }


class TrendFollowingStrategy(StrategyEngine):
    """
    趋势跟踪策略
    
    基于移动平均线的简单趋势策略
    """
    
    def __init__(self):
        super().__init__(
            name="趋势跟踪策略",
            description="基于移动平均线判断趋势，顺势而为"
        )
        self.short_period = 5   # 短期均线
        self.long_period = 20   # 长期均线
    
    def calculate_ma(self, prices: List[float], period: int) -> Optional[float]:
        """
        计算移动平均线
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            移动平均值
        """
        if len(prices) < period:
            return None
        
        return statistics.mean(prices[-period:])
    
    def analyze(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析股票数据
        
        Args:
            historical_data: 历史数据
            
        Returns:
            分析结果
        """
        if len(historical_data) < self.long_period:
            return {"error": "数据不足"}
        
        # 提取收盘价
        close_prices = [d["close"] for d in historical_data]
        
        # 计算均线
        ma_short = self.calculate_ma(close_prices, self.short_period)
        ma_long = self.calculate_ma(close_prices, self.long_period)
        
        # 当前价格
        current_price = close_prices[-1]
        
        # 判断趋势
        if ma_short and ma_long:
            if ma_short > ma_long:
                trend = "上涨"
                strength = (ma_short - ma_long) / ma_long * 100
            else:
                trend = "下跌"
                strength = (ma_long - ma_short) / ma_long * 100
        else:
            trend = "不明"
            strength = 0
        
        return {
            "current_price": current_price,
            "ma_short": ma_short,
            "ma_long": ma_long,
            "trend": trend,
            "trend_strength": round(strength, 2),
            "signal_strength": min(abs(strength), 100),
        }
    
    def generate_signal(self, analysis: Dict[str, Any]) -> str:
        """
        生成交易信号
        
        金叉买入，死叉卖出
        
        Args:
            analysis: 分析结果
            
        Returns:
            交易信号
        """
        if "error" in analysis:
            return "hold"
        
        ma_short = analysis.get("ma_short", 0)
        ma_long = analysis.get("ma_long", 0)
        strength = analysis.get("trend_strength", 0)
        
        # 金叉：短期均线上穿长期均线
        if ma_short > ma_long and strength > 2:
            return "buy"
        
        # 死叉：短期均线下穿长期均线
        if ma_short < ma_long and strength > 2:
            return "sell"
        
        return "hold"


class ValueInvestingStrategy(StrategyEngine):
    """
    价值投资策略
    
    基于公司基本面的价值投资
    """
    
    def __init__(self):
        super().__init__(
            name="价值投资策略",
            description="基于公司基本面选择低估值优质股票"
        )
    
    def analyze(self, company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析公司基本面
        
        Args:
            company_info: 公司信息
            
        Returns:
            分析结果
        """
        pe_ratio = company_info.get("pe_ratio", 0)
        pb_ratio = company_info.get("pb_ratio", 0)
        
        # 估值评分
        pe_score = 100 - min(pe_ratio, 100)  # PE越低越好
        pb_score = 100 - min(pb_ratio * 20, 100)  # PB越低越好
        
        value_score = (pe_score + pb_score) / 2
        
        return {
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "value_score": round(value_score, 2),
            "valuation": "低估" if value_score > 60 else "合理" if value_score > 40 else "高估",
        }
    
    def generate_signal(self, analysis: Dict[str, Any]) -> str:
        """生成交易信号"""
        value_score = analysis.get("value_score", 0)
        
        if value_score > 70:
            return "buy"
        elif value_score < 30:
            return "sell"
        else:
            return "hold"


class AIStrategy(StrategyEngine):
    """
    AI策略
    
    基于大语言模型的智能投资策略
    根据需求3.7: 自我学习、自我进化
    """
    
    def __init__(self, llm_url: str = "http://localhost:11434"):
        super().__init__(
            name="AI智能策略",
            description="基于大语言模型的智能分析和决策"
        )
        self.llm_url = llm_url
    
    def analyze_with_llm(
        self,
        stock_data: Dict[str, Any],
        market_news: List[str] = None
    ) -> Dict[str, Any]:
        """
        使用LLM分析股票
        
        Args:
            stock_data: 股票数据
            market_news: 市场新闻
            
        Returns:
            LLM分析结果
        """
        # TODO: 调用Ollama API进行智能分析
        # 根据需求3.8: 与RAG关联，检索历史数据
        
        prompt = f"""
        请分析以下股票数据：
        
        股票代码：{stock_data.get('code')}
        当前价格：{stock_data.get('current_price')}
        涨跌幅：{stock_data.get('change_percent')}%
        市盈率：{stock_data.get('pe_ratio')}
        市净率：{stock_data.get('pb_ratio')}
        
        请给出：
        1. 技术面分析
        2. 基本面分析
        3. 投资建议（买入/卖出/持有）
        4. 风险提示
        """
        
        # 简化返回（实际需要调用LLM）
        return {
            "analysis": "基于当前数据分析...",
            "recommendation": "hold",
            "confidence": 75,
            "risks": ["市场波动风险", "政策风险"],
        }
    
    def analyze(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析股票"""
        return self.analyze_with_llm(stock_data)
    
    def generate_signal(self, analysis: Dict[str, Any]) -> str:
        """生成信号"""
        return analysis.get("recommendation", "hold")


class StrategyManager:
    """
    策略管理器
    
    管理多个策略，综合决策
    """
    
    def __init__(self):
        """初始化策略管理器"""
        self.strategies = {
            "trend": TrendFollowingStrategy(),
            "value": ValueInvestingStrategy(),
            "ai": AIStrategy(),
        }
        self.active_strategies = ["trend", "value"]  # 默认激活的策略
    
    def add_strategy(self, key: str, strategy: StrategyEngine):
        """添加策略"""
        self.strategies[key] = strategy
    
    def enable_strategy(self, key: str):
        """启用策略"""
        if key in self.strategies and key not in self.active_strategies:
            self.active_strategies.append(key)
    
    def disable_strategy(self, key: str):
        """禁用策略"""
        if key in self.active_strategies:
            self.active_strategies.remove(key)
    
    def get_combined_signal(
        self,
        stock_code: str,
        stock_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取综合信号
        
        综合多个策略的判断
        
        Args:
            stock_code: 股票代码
            stock_data: 股票数据
            
        Returns:
            综合信号和分析
        """
        signals = {}
        analyses = {}
        
        for key in self.active_strategies:
            if key not in self.strategies:
                continue
            
            strategy = self.strategies[key]
            analysis = strategy.analyze(stock_data)
            signal = strategy.generate_signal(analysis)
            
            signals[key] = signal
            analyses[key] = analysis
        
        # 综合判断（简单投票）
        buy_votes = sum(1 for s in signals.values() if s == "buy")
        sell_votes = sum(1 for s in signals.values() if s == "sell")
        
        if buy_votes > sell_votes:
            final_signal = "buy"
        elif sell_votes > buy_votes:
            final_signal = "sell"
        else:
            final_signal = "hold"
        
        return {
            "stock_code": stock_code,
            "final_signal": final_signal,
            "individual_signals": signals,
            "analyses": analyses,
            "confidence": round(max(buy_votes, sell_votes) / len(signals) * 100, 2) if signals else 0,
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_all_strategies_performance(self) -> Dict[str, Any]:
        """
        获取所有策略的表现
        
        Returns:
            策略表现汇总
        """
        performance = {}
        for key, strategy in self.strategies.items():
            performance[key] = {
                "name": strategy.name,
                "metrics": strategy.get_performance_metrics(),
            }
        
        return performance

