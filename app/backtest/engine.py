import backtrader as bt
from typing import Type, Dict, Any, List, Optional
import logging
from app.backtest.analyzer import BacktestAnalyzer
from app.backtest.exceptions import BacktestError

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, initial_cash: float = 100000.0, commission: float = 0.0003):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        self.initial_cash = initial_cash
        
        # Add default analyzers
        # timeframe=bt.TimeFrame.Years to get annual return? No, keep it simple for now.
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, compression=1, riskfreerate=0.02)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        # self.cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    def add_data(self, data: bt.feeds.PandasData):
        self.cerebro.adddata(data)

    def run(self, strategy_cls: Type[bt.Strategy], **kwargs) -> Dict[str, Any]:
        """
        Run the backtest with the given strategy and parameters
        """
        try:
            logger.info(f"Starting backtest with strategy {strategy_cls.__name__} and params {kwargs}")
            
            # Add strategy with parameters
            self.cerebro.addstrategy(strategy_cls, **kwargs)
            
            # Run backtest
            results = self.cerebro.run()
            
            if not results:
                raise BacktestError("Backtest produced no results")
                
            # Parse results (assuming single strategy run)
            strat = results[0]
            parsed_results = BacktestAnalyzer.parse_results(strat)
            
            # Add final portfolio value and PnL
            final_value = self.cerebro.broker.getvalue()
            pnl = final_value - self.initial_cash
            return_pct = (pnl / self.initial_cash) * 100
            
            parsed_results['metrics']['initial_cash'] = self.initial_cash
            parsed_results['metrics']['final_value'] = final_value
            parsed_results['metrics']['pnl'] = pnl
            parsed_results['metrics']['return_pct'] = return_pct
            
            logger.info(f"Backtest completed. Final Value: {final_value:.2f}, Return: {return_pct:.2f}%")
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            raise BacktestError(f"Backtest execution failed: {e}")
