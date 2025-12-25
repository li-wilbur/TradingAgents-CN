from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.backtest.strategies.registry import StrategyRegistry
from app.backtest.feeds import get_data_feed
from app.backtest.engine import BacktestEngine
from app.backtest.exceptions import BacktestError

logger = logging.getLogger(__name__)

router = APIRouter()

class BacktestRequest(BaseModel):
    strategy_id: str
    symbol: str
    start_date: str
    end_date: str
    initial_cash: float = 100000.0
    commission: float = 0.0003
    params: Dict[str, Any] = {}

class BacktestResponse(BaseModel):
    status: str
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.get("/strategies", response_model=List[Dict[str, Any]])
async def get_strategies():
    """
    Get all available strategies and their parameter schemas.
    """
    # Trigger discovery (in case new files were added)
    StrategyRegistry.discover_strategies()
    return StrategyRegistry.get_all_strategies()

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest synchronously.
    For long-running backtests, this should be converted to an async background task 
    that updates a job status in DB. For MVP, we run it directly.
    """
    try:
        # 1. Get Strategy Class
        strategy_cls = StrategyRegistry.get_strategy(request.strategy_id)
        if not strategy_cls:
            raise HTTPException(status_code=404, detail=f"Strategy {request.strategy_id} not found")
            
        # 2. Get Data Feed
        feed = await get_data_feed(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # 3. Initialize Engine
        engine = BacktestEngine(
            initial_cash=request.initial_cash,
            commission=request.commission
        )
        engine.add_data(feed)
        
        # 4. Run Backtest
        # Pass params as kwargs
        results = engine.run(strategy_cls, **request.params)
        
        return BacktestResponse(
            status="success",
            metrics=results['metrics']
        )
        
    except BacktestError as e:
        logger.error(f"Backtest failed: {e}")
        return BacktestResponse(status="failed", error=str(e))
    except Exception as e:
        logger.exception("Unexpected error during backtest")
        raise HTTPException(status_code=500, detail=str(e))
