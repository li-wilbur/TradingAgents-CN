import logging
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.services.paper_trading.models import PaperAccount, PaperPosition, PaperOrder

logger = logging.getLogger(__name__)

class VirtualBroker:
    """
    Virtual Broker for Paper Trading.
    Handles order execution and account management against MongoDB.
    """
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
        
    async def initialize(self):
        if not self.db:
            self.db = get_database()
            # Ensure indexes
            await self.db.paper_accounts.create_index([("user_id", 1), ("strategy_id", 1)], unique=True)
            await self.db.paper_orders.create_index("account_id")
            
    async def get_account(self, user_id: str, strategy_id: str) -> Optional[PaperAccount]:
        await self.initialize()
        doc = await self.db.paper_accounts.find_one({
            "user_id": user_id, 
            "strategy_id": strategy_id
        })
        if doc:
            return PaperAccount(**doc)
        return None

    async def create_account(self, user_id: str, strategy_id: str, initial_capital: float = 100000.0) -> PaperAccount:
        await self.initialize()
        
        # Check if exists
        existing = await self.get_account(user_id, strategy_id)
        if existing:
            return existing
            
        account = PaperAccount(
            user_id=user_id,
            strategy_id=strategy_id,
            initial_capital=initial_capital,
            cash=initial_capital,
            total_assets=initial_capital
        )
        
        await self.db.paper_accounts.insert_one(account.model_dump())
        logger.info(f"Created paper account for user {user_id}, strategy {strategy_id}")
        return account

    async def execute_order(self, user_id: str, strategy_id: str, symbol: str, 
                          side: str, quantity: int, price: float, commission_rate: float = 0.0003) -> Optional[PaperOrder]:
        """
        Execute a simulated order.
        Atomic operation is simulated via logical checks (Mongo Transaction recommended for production).
        """
        await self.initialize()
        
        account_data = await self.db.paper_accounts.find_one({"user_id": user_id, "strategy_id": strategy_id})
        if not account_data:
            logger.error(f"Account not found for {user_id}/{strategy_id}")
            return None
            
        account = PaperAccount(**account_data)
        commission = quantity * price * commission_rate
        total_cost = (quantity * price)
        
        # 1. Validation
        if side == "BUY":
            cost_with_comm = total_cost + commission
            if account.cash < cost_with_comm:
                logger.warning(f"Insufficient funds: {account.cash} < {cost_with_comm}")
                return None
        elif side == "SELL":
            if symbol not in account.positions or account.positions[symbol].quantity < quantity:
                logger.warning(f"Insufficient position: {symbol}")
                return None
                
        # 2. Update Account State
        if side == "BUY":
            account.cash -= (total_cost + commission)
            
            # Update Position
            if symbol in account.positions:
                pos = account.positions[symbol]
                # Weighted average cost
                new_cost = ((pos.cost_price * pos.quantity) + total_cost) / (pos.quantity + quantity)
                pos.quantity += quantity
                pos.cost_price = new_cost
            else:
                account.positions[symbol] = PaperPosition(
                    symbol=symbol,
                    quantity=quantity,
                    cost_price=price
                )
                
        elif side == "SELL":
            account.cash += (total_cost - commission)
            
            # Update Position
            pos = account.positions[symbol]
            pos.quantity -= quantity
            if pos.quantity == 0:
                del account.positions[symbol]
        
        account.updated_at = datetime.utcnow()
        
        # 3. Create Order Record
        order = PaperOrder(
            account_id=str(account_data['_id']),
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            commission=commission,
            status="FILLED"
        )
        
        # 4. Persist Changes (Naive implementation without transaction for simplicity in MVP)
        await self.db.paper_accounts.replace_one(
            {"_id": account_data['_id']}, 
            account.model_dump()
        )
        await self.db.paper_orders.insert_one(order.model_dump())
        
        logger.info(f"Executed {side} {symbol}: {quantity} @ {price}")
        return order
