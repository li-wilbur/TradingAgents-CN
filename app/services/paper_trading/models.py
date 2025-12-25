from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class PaperPosition(BaseModel):
    symbol: str
    quantity: int
    cost_price: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None

class PaperAccount(BaseModel):
    user_id: str
    strategy_id: str
    status: str = "active" # active, stopped
    initial_capital: float = 100000.0
    cash: float = 100000.0
    total_assets: float = 100000.0
    positions: Dict[str, PaperPosition] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class PaperOrder(BaseModel):
    account_id: str
    symbol: str
    side: str # BUY, SELL
    order_type: str = "MARKET" # MARKET, LIMIT
    quantity: int
    price: float
    commission: float = 0.0
    status: str = "FILLED" # FILLED, REJECTED
    reason: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)
