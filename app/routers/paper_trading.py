from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.services.paper_trading.broker import VirtualBroker
from app.services.paper_trading.models import PaperAccount, PaperOrder

logger = logging.getLogger(__name__)

router = APIRouter()
broker = VirtualBroker()

class CreateAccountRequest(BaseModel):
    user_id: str
    strategy_id: str
    initial_capital: float = 100000.0

@router.post("/accounts", response_model=PaperAccount)
async def create_paper_account(request: CreateAccountRequest):
    """
    Create a new paper trading account.
    """
    try:
        account = await broker.create_account(
            user_id=request.user_id,
            strategy_id=request.strategy_id,
            initial_capital=request.initial_capital
        )
        return account
    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{user_id}/{strategy_id}", response_model=PaperAccount)
async def get_paper_account(user_id: str, strategy_id: str):
    """
    Get paper trading account details.
    """
    account = await broker.get_account(user_id, strategy_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
