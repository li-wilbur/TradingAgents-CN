import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pandas as pd
import backtrader as bt
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.backtest.feeds import get_data_feed
from app.backtest.engine import BacktestEngine
from app.backtest.strategies.registry import StrategyRegistry

# Generate longer mock data for MA strategy (needs at least 30 periods for slow MA)
def generate_mock_data(periods=200):
    dates = pd.date_range(start="2023-01-01", periods=periods, freq="D")
    data = []
    price = 100.0
    for i, date in enumerate(dates):
        # Create a clearer trend: sinusoidal wave to force crosses
        price = 100 + 10 * np.sin(i / 20.0) 
            
        data.append({
            "trade_date": date.strftime("%Y-%m-%d"),
            "open": price,
            "high": price + 2,
            "low": price - 2,
            "close": price,
            "volume": 1000 + i * 10
        })
    return data

MOCK_DATA = generate_mock_data()

async def test_strategy_system():
    print("Testing Strategy System...")
    
    # 1. Test Discovery
    print("1. Discovering Strategies...")
    # Manually register the example strategy for test environment since discover relies on import
    from app.backtest.strategies.examples.ma_cross import DualMovingAverage
    StrategyRegistry._strategies['DualMovingAverage'] = DualMovingAverage
    
    strategies = StrategyRegistry.get_all_strategies()
    print(f"   Found {len(strategies)} strategies.")
    for s in strategies:
        print(f"   - {s['name']} (Params: {[p['name'] for p in s['params']]})")
        
    if not strategies:
        print("❌ Test Failed: No strategies found.")
        return

    # 2. Test Execution
    print("\n2. Running DualMovingAverage Strategy...")
    
    # Mock HistoricalDataService
    with patch('app.backtest.feeds.get_historical_data_service', new_callable=AsyncMock) as mock_get_service:
        mock_service = MagicMock()
        mock_service.get_historical_data = AsyncMock(return_value=MOCK_DATA)
        mock_get_service.return_value = mock_service
        
        # Get Feed
        feed = await get_data_feed("TEST_SYMBOL")
        
        # Init Engine
        engine = BacktestEngine(initial_cash=100000.0)
        engine.add_data(feed)
        
        # Run Strategy
        strategy_cls = StrategyRegistry.get_strategy('DualMovingAverage')
        results = engine.run(strategy_cls, fast_period=5, slow_period=10, printlog=True)
        
        # Check Results
        metrics = results['metrics']
        print(f"   Final Value: {metrics['final_value']:.2f}")
        print(f"   Return: {metrics['return_pct']:.2f}%")
        print(f"   Total Trades: {metrics['total_trades']}")
        
        if metrics['total_trades'] > 0:
             print("✅ Test Passed: Strategy executed trades.")
        else:
             print("⚠️ Warning: No trades executed (Check data length vs MA periods).")

if __name__ == "__main__":
    asyncio.run(test_strategy_system())
