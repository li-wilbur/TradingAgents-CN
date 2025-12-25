import backtrader as bt
from typing import Dict, Any

class BacktestAnalyzer:
    @staticmethod
    def parse_results(strategy: bt.Strategy) -> Dict[str, Any]:
        """
        Parse strategy execution results into a dictionary
        """
        results = {
            "params": strategy.p._getkwargs(),
            "metrics": {},
            # "trades": [] # Detailed trade log to be implemented later
        }
        
        # Parse Sharpe Ratio
        if hasattr(strategy.analyzers, 'sharpe'):
            sharpe = strategy.analyzers.sharpe.get_analysis()
            # Sharpe ratio can be None if not enough data
            results['metrics']['sharpe_ratio'] = sharpe.get('sharperatio', 0.0) if sharpe.get('sharperatio') is not None else 0.0
            
        # Parse DrawDown
        if hasattr(strategy.analyzers, 'drawdown'):
            dd = strategy.analyzers.drawdown.get_analysis()
            results['metrics']['max_drawdown'] = dd.get('max', {}).get('drawdown', 0.0)
            results['metrics']['max_drawdown_len'] = dd.get('max', {}).get('len', 0)
            
        # Parse Returns
        if hasattr(strategy.analyzers, 'returns'):
            ret = strategy.analyzers.returns.get_analysis()
            # rtot is logarithmic return, convert to simple return? 
            # Actually TimeReturn analyzer returns a dict of dates if timeframe is set, 
            # or total return if not.
            # Let's use simple return calculation from broker value in engine instead for total return.
            # Here we might capture annual return if available.
            pass 
            
        # Parse Trade Analysis
        if hasattr(strategy.analyzers, 'trades'):
            trades = strategy.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            results['metrics']['total_trades'] = total_trades
            results['metrics']['won_trades'] = trades.get('won', {}).get('total', 0)
            results['metrics']['lost_trades'] = trades.get('lost', {}).get('total', 0)
            
            # Win Rate
            results['metrics']['win_rate'] = (results['metrics']['won_trades'] / total_trades) if total_trades > 0 else 0.0
            
            # Profit Factor
            gross_won = trades.get('won', {}).get('pnl', {}).get('total', 0.0)
            gross_lost = abs(trades.get('lost', {}).get('pnl', {}).get('total', 0.0))
            results['metrics']['profit_factor'] = (gross_won / gross_lost) if gross_lost > 0 else float('inf') if gross_won > 0 else 0.0

        return results
