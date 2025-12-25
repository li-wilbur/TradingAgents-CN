import backtrader as bt
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BaseStrategy(bt.Strategy):
    """
    Base strategy class that simplifies order management and logging.
    All custom strategies should inherit from this class.
    """
    
    # Metadata for the strategy registry
    metadata = {
        "name": "Base Strategy",
        "description": "Base class for all strategies",
        "author": "TradingAgents",
        "version": "1.0"
    }
    
    params = (
        ('printlog', False),
    )

    def __init__(self):
        self.orders = {}  # Keep track of orders
        self.order = None # Current pending order
        self.buy_price = None
        self.buy_comm = None
        self.trades_history = []

    def log(self, txt: str, dt=None):
        """Logging function for this strategy"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            logger.info(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """
        Standard order processing:
        - Logs order submission/acceptance
        - Checks for completion/cancellation
        - Records execution price and commission
        """
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                )
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.getstatusname()}')

        # Write down: no pending order
        self.orders[order.ref] = None
        self.order = None

    def notify_trade(self, trade):
        """
        Standard trade processing:
        - Logs profit/loss on closed trades
        - Records trade history
        """
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
        
        self.trades_history.append({
            "date": self.datas[0].datetime.date(0).isoformat(),
            "pnl": trade.pnl,
            "pnlcomm": trade.pnlcomm,
            "price": trade.price,
            "size": trade.size
        })

    def buy_signal(self):
        """Helper to execute a buy (long)"""
        # Default implementation uses 95% of available cash to buy
        # Can be overridden or customized via sizer
        self.order = self.buy()

    def sell_signal(self):
        """Helper to execute a sell (close position)"""
        self.order = self.close()
        
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Extracts strategy parameters and metadata to generate a frontend schema.
        This allows the frontend to dynamically build configuration forms.
        """
        schema = {
            "id": cls.__name__,
            "name": cls.metadata.get("name", cls.__name__),
            "description": cls.metadata.get("description", ""),
            "params": []
        }
        
        # Parse params
        # bt.Strategy.params is a dict-like object (AutoInfoClass)
        # We need to access the default values
        default_params = cls.params._gettuple()
        
        for key, value in default_params:
            if key == 'printlog': continue # Skip system params
            
            param_def = {
                "name": key,
                "default": value,
                "type": type(value).__name__
            }
            schema["params"].append(param_def)
            
        return schema
