import asyncio
import logging
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.paper_trading.broker import VirtualBroker
from app.services.paper_trading.data_pump import RealtimeDataPump
from app.services.paper_trading.signal_analyzer import SignalAnalyzer
from app.backtest.feeds import get_data_feed
from app.backtest.engine import BacktestEngine
from app.backtest.strategies.registry import StrategyRegistry
# Note: We need a StrategyRunner that can take a strategy class, feed it data, and execute one step.
# This is complex because Backtrader is designed for batch processing.
# For this MVP, we will implement a simplified 'Signal Check' logic instead of full Backtrader engine for Paper Trading.
# Or we can run Backtrader in a 'replay' mode where we load history + today, and see if it generates a signal on the last bar.

logger = logging.getLogger(__name__)

class PaperScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.broker = VirtualBroker()
        self.running_tasks = [] # List of active paper trading tasks

    def start(self):
        # Schedule daily check at 14:55 (China Market Close)
        self.scheduler.add_job(
            self.run_daily_check,
            CronTrigger(hour=14, minute=55, timezone='Asia/Shanghai'),
            id='daily_strategy_check',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Paper Trading Scheduler started.")

    async def run_daily_check(self):
        """
        Execute daily strategy check for all active paper accounts.
        """
        logger.info("Starting daily strategy check...")
        
        try:
            # 1. Get all active paper accounts (simplified, should filter by status='active')
            cursor = self.broker.db.paper_accounts.find({"status": "active"})
            async for account_doc in cursor:
                await self._process_account(account_doc)
                
        except Exception as e:
            logger.error(f"Daily check failed: {e}")

    async def _process_account(self, account_doc: dict):
        """Process a single account for daily trading"""
        user_id = account_doc['user_id']
        strategy_id = account_doc['strategy_id']
        logger.info(f"Processing account {user_id}/{strategy_id}...")
        
        try:
            # 1. Resolve Strategy Class
            # Assuming strategy_id matches the class name in registry
            # In real system, we might store 'strategy_name' in account
            strategy_cls = StrategyRegistry.get_strategy(strategy_id)
            if not strategy_cls:
                logger.error(f"Strategy {strategy_id} not found in registry")
                return

            # 2. Get Data (History + Today)
            # We need enough history for indicators (e.g. 100 days)
            # In a real implementation, we would query HistoricalDataService for last N days
            # AND fetch real-time data for 'today' via DataPump
            
            # For this MVP, let's assume HistoricalDataService already has today's data 
            # (e.g. updated by a separate crawler job)
            # So we just load the last 100 bars from DB.
            
            # TODO: Get symbol from account settings or strategy default? 
            # For now, let's assume strategy is single-symbol and we pick one from current positions 
            # or a default one. This is a simplification.
            symbol = "000001.SZ" # Hardcoded for MVP demo
            
            # 3. Simulate Strategy Execution
            feed = await get_data_feed(symbol, limit=100) # Get last 100 bars
            
            # Use a fresh Cerebro instance directly to have full control
            import backtrader as bt
            cerebro = bt.Cerebro()
            cerebro.adddata(feed)
            cerebro.broker.setcash(account_doc['cash'])
            
            # Add the strategy
            # Note: We need to pass params from account_doc if stored, or defaults
            cerebro.addstrategy(strategy_cls)
            
            # Add Signal Analyzer to capture orders
            cerebro.addanalyzer(SignalAnalyzer, _name='signals')
            
            logger.info(f"Running strategy check for {symbol}...")
            results = cerebro.run()
            
            # 4. Process Signals
            if results:
                strat = results[0]
                orders = strat.analyzers.signals.get_analysis()
                
                # Check if the LAST order was generated on the LAST bar (today)
                # Since we are running on historical data + today, we check if an order was created at the end.
                # However, backtrader processes all data. We need to know if an order was created for the *next* day (tomorrow) 
                # or executed today.
                
                # In Backtrader, orders created in next() are for the next bar.
                # So if we run up to Today, and next() calls buy(), it means we want to buy Tomorrow Open (or Today Close if using Cheating)
                
                # For this MVP, if we find any submitted order in the analyzer that corresponds to the end of data:
                if orders:
                    last_order = orders[-1]
                    # Check timestamp if possible, or just assume it's fresh since we run daily
                    
                    side = "BUY" if last_order.isbuy() else "SELL"
                    quantity = last_order.size
                    price = last_order.created.price # Limit price or None for Market
                    
                    # If price is None (Market Order), use current close
                    if not price:
                        price = feed.close[0]
                        
                    logger.info(f"Signal detected: {side} {quantity} @ {price}")
                    
                    # 5. Execute via Virtual Broker
                    await self.broker.execute_order(
                        user_id=user_id,
                        strategy_id=strategy_id,
                        symbol=symbol,
                        side=side,
                        quantity=abs(quantity),
                        price=price
                    )
            
        except Exception as e:
            logger.error(f"Error processing account {user_id}/{strategy_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error processing account {user_id}/{strategy_id}: {e}")
