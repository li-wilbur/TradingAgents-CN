class BacktestError(Exception):
    """Base exception for backtest module"""
    pass

class DataFeedError(BacktestError):
    """Error related to data feeds"""
    pass

class StrategyError(BacktestError):
    """Error related to strategy execution"""
    pass
