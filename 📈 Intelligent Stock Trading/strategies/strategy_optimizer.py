"""
投资策略优化器
- 策略回测
- 参数优化
- 绩效评估
- 自适应调整
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np


class StrategyOptimizer:
    """策略优化器"""
    
    def __init__(self):
        # 策略库
        self.strategies = {}
        
        # 优化历史
        self.optimization_history = []
    
    # ============ 策略回测 ============
    
    def backtest_strategy(
        self,
        strategy_name: str,
        strategy_params: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        initial_capital: float = 1000000
    ) -> Dict[str, Any]:
        """
        策略回测
        
        Args:
            strategy_name: 策略名称
            strategy_params: 策略参数
            historical_data: 历史数据
            initial_capital: 初始资金
        
        Returns:
            回测结果
        """
        try:
            # 简化的回测实现
            capital = initial_capital
            positions = {}
            trades = []
            
            # 模拟交易
            for i, data in enumerate(historical_data):
                # 根据策略生成信号
                signal = self._generate_strategy_signal(
                    strategy_name,
                    strategy_params,
                    data,
                    positions
                )
                
                if signal:
                    # 执行模拟交易
                    if signal['action'] == 'buy' and capital >= signal['amount']:
                        positions[signal['stock_code']] = {
                            "quantity": signal['quantity'],
                            "cost": signal['price'],
                            "buy_date": data['date']
                        }
                        capital -= signal['amount']
                        trades.append({**signal, "date": data['date']})
                    
                    elif signal['action'] == 'sell' and signal['stock_code'] in positions:
                        position = positions[signal['stock_code']]
                        sell_amount = position['quantity'] * signal['price']
                        capital += sell_amount
                        profit = sell_amount - (position['quantity'] * position['cost'])
                        
                        trades.append({
                            **signal,
                            "date": data['date'],
                            "profit": profit
                        })
                        del positions[signal['stock_code']]
            
            # 计算最终市值
            final_value = capital
            for stock_code, position in positions.items():
                final_price = historical_data[-1].get('prices', {}).get(stock_code, position['cost'])
                final_value += position['quantity'] * final_price
            
            # 计算收益率
            total_return = (final_value - initial_capital) / initial_capital * 100
            
            # 计算最大回撤
            max_drawdown = self._calculate_max_drawdown(trades)
            
            # 计算夏普比率
            sharpe_ratio = self._calculate_sharpe_ratio(trades)
            
            return {
                "success": True,
                "strategy_name": strategy_name,
                "backtest_result": {
                    "initial_capital": initial_capital,
                    "final_value": final_value,
                    "total_return": float(total_return),
                    "total_trades": len(trades),
                    "max_drawdown": float(max_drawdown),
                    "sharpe_ratio": float(sharpe_ratio),
                    "trades": trades
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 参数优化 ============
    
    def optimize_strategy_params(
        self,
        strategy_name: str,
        param_ranges: Dict[str, tuple],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        优化策略参数
        
        Args:
            strategy_name: 策略名称
            param_ranges: 参数范围 {"param_name": (min, max, step)}
            historical_data: 历史数据
        
        Returns:
            最优参数
        """
        try:
            best_params = None
            best_return = float('-inf')
            best_result = None
            
            # 网格搜索（简化版）
            test_count = 0
            max_tests = 20  # 限制测试次数
            
            # 生成参数组合（示例：只测试几组）
            param_combinations = self._generate_param_combinations(param_ranges, max_tests)
            
            for params in param_combinations:
                # 回测
                result = self.backtest_strategy(
                    strategy_name,
                    params,
                    historical_data
                )
                
                if result['success']:
                    returns = result['backtest_result']['total_return']
                    
                    if returns > best_return:
                        best_return = returns
                        best_params = params
                        best_result = result['backtest_result']
                
                test_count += 1
            
            # 记录优化历史
            optimization_record = {
                "strategy_name": strategy_name,
                "param_ranges": param_ranges,
                "best_params": best_params,
                "best_return": float(best_return),
                "tests_count": test_count,
                "optimized_at": datetime.utcnow().isoformat()
            }
            
            self.optimization_history.append(optimization_record)
            
            return {
                "success": True,
                "optimization": optimization_record,
                "best_result": best_result,
                "message": f"参数优化完成，最优收益率: {best_return:.2f}%"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 内部辅助方法 ============
    
    def _generate_strategy_signal(
        self,
        strategy_name: str,
        params: Dict[str, Any],
        data: Dict[str, Any],
        positions: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成策略信号（简化实现）"""
        # 这里是简化的策略逻辑示例
        # 实际应该根据不同策略实现不同逻辑
        
        if strategy_name == "moving_average":
            # 移动平均策略示例
            ma_short = params.get('ma_short', 5)
            ma_long = params.get('ma_long', 20)
            
            # 简化处理，实际应计算真实均线
            if np.random.random() > 0.7:  # 模拟买入信号
                return {
                    "action": "buy",
                    "stock_code": "600000",
                    "price": data.get('price', 10.0),
                    "quantity": 100,
                    "amount": 1000
                }
        
        return None
    
    def _calculate_max_drawdown(self, trades: List[Dict[str, Any]]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0.0
        
        # 简化计算
        profits = [t.get('profit', 0) for t in trades if 'profit' in t]
        
        if not profits:
            return 0.0
        
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max * 100
        
        return abs(float(np.min(drawdown))) if len(drawdown) > 0 else 0.0
    
    def _calculate_sharpe_ratio(self, trades: List[Dict[str, Any]]) -> float:
        """计算夏普比率"""
        if not trades:
            return 0.0
        
        profits = [t.get('profit', 0) for t in trades if 'profit' in t]
        
        if not profits:
            return 0.0
        
        returns = np.array(profits)
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        sharpe = (avg_return / std_return) if std_return > 0 else 0.0
        
        return float(sharpe)
    
    def _generate_param_combinations(
        self,
        param_ranges: Dict[str, tuple],
        max_count: int
    ) -> List[Dict[str, Any]]:
        """生成参数组合"""
        # 简化实现：均匀采样
        combinations = []
        
        # 示例：生成几组测试参数
        for i in range(min(max_count, 10)):
            params = {}
            for param_name, (min_val, max_val, step) in param_ranges.items():
                # 均匀采样
                value = min_val + (max_val - min_val) * (i / max_count)
                params[param_name] = round(value / step) * step
            
            combinations.append(params)
        
        return combinations
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self.optimization_history[-limit:]


# 全局实例
strategy_optimizer = StrategyOptimizer()

