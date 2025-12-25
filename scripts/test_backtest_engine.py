import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pandas as pd
import backtrader as bt

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.backtest.feeds import get_data_feed
from app.backtest.engine import BacktestEngine

# Mock data
MOCK_DATA = [
    {"trade_date": "2023-01-01", "open": 100, "high": 105, "low": 99, "close": 102, "volume": 1000},
    {"trade_date": "2023-01-02", "open": 102, "high": 108, "low": 101, "close": 106, "volume": 1200},
    {"trade_date": "2023-01-03", "open": 106, "high": 110, "low": 105, "close": 108, "volume": 1500},
    {"trade_date": "2023-01-04", "open": 108, "high": 109, "low": 100, "close": 101, "volume": 2000},
    {"trade_date": "2023-01-05", "open": 101, "high": 103, "low": 98, "close": 99, "volume": 800},
]

class TestStrategy(bt.Strategy):
    def next(self):
        # Simple Buy and Hold: Buy on first day
        if len(self) == 1:
            self.buy()

async def test_engine():
    print("Testing Backtest Engine...")
    
    # Mock HistoricalDataService
    with patch('app.backtest.feeds.get_historical_data_service', new_callable=AsyncMock) as mock_get_service:
        # Create mock service
        mock_service = MagicMock()
        # Mock get_historical_data to be an async method returning MOCK_DATA
        mock_service.get_historical_data = AsyncMock(return_value=MOCK_DATA)
        
        mock_get_service.return_value = mock_service
        
        # 1. Get Data Feed
        print("1. Creating Data Feed...")
        feed = await get_data_feed("TEST_SYMBOL")
        print("   Data Feed created successfully.")
        
        # 2. Initialize Engine
        print("2. Initializing Backtest Engine...")
        engine = BacktestEngine(initial_cash=10000.0)
        engine.add_data(feed)
        print("   Engine initialized.")
        
        # 3. Run Strategy
        print("3. Running Test Strategy...")
        results = engine.run(TestStrategy)
        
        # 4. Check Results
        print("4. Results:")
        metrics = results['metrics']
        print(f"   Initial Cash: {metrics['initial_cash']}")
        print(f"   Final Value: {metrics['final_value']}")
        print(f"   PnL: {metrics['pnl']}")
        print(f"   Return: {metrics['return_pct']:.2f}%")
        print(f"   Total Trades: {metrics['total_trades']}")
        
        if metrics['pnl'] != 0:
            print("✅ Test Passed: Engine ran and produced PnL.")
        else:
            print("❌ Test Failed: PnL is 0 (Strategy might not have executed).")

if __name__ == "__main__":
    asyncio.run(test_engine())
