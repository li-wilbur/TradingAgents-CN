import backtrader as bt
from app.backtest.strategies.base import BaseStrategy

class DualMovingAverage(BaseStrategy):
    """
    A simple dual moving average crossover strategy.
    Buys when the short-term MA crosses above the long-term MA.
    Sells when the short-term MA crosses below the long-term MA.
    """
    
    metadata = {
        "name": "Dual Moving Average",
        "description": "Trend following strategy using two moving averages",
        "author": "TradingAgents",
        "version": "1.0"
    }
    
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )

    def __init__(self):
        super().__init__()
        
        # Add indicators
        self.fast_ma = bt.indicators.SMA(
            self.data.close, 
            period=self.params.fast_period,
            plotname='Fast MA'
        )
        self.slow_ma = bt.indicators.SMA(
            self.data.close, 
            period=self.params.slow_period,
            plotname='Slow MA'
        )
        
        # Crossover signal: 1 if fast crosses above slow, -1 if below
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.data.close[0])

        # Check for open orders
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # We are not in the market, look for a signal to BUY
            if self.crossover > 0:
                self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
                # Keep track of the created order to avoid a 2nd order
                self.buy_signal()
        else:
            # We are already in the market, look for a signal to SELL
            if self.crossover < 0:
                self.log(f'SELL CREATE, {self.data.close[0]:.2f}')
                # Keep track of the created order to avoid a 2nd order
                self.sell_signal()
