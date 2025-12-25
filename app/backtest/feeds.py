import pandas as pd
import backtrader as bt
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from app.services.historical_data_service import get_historical_data_service
from app.backtest.exceptions import DataFeedError

logger = logging.getLogger(__name__)

class MongoPandasData(bt.feeds.PandasData):
    """
    Backtrader Data Feed for MongoDB data
    Expects a DataFrame with a datetime index and standard OHLCV columns
    """
    params = (
        ('datetime', None), # datetime is the index
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1), # -1 means not present
    )

async def get_data_feed(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_source: Optional[str] = None,
    period: str = 'daily'
) -> bt.feeds.PandasData:
    """
    Fetch data from HistoricalDataService and return a Backtrader Data Feed
    """
    try:
        service = await get_historical_data_service()
        
        # Fetch data
        records = await service.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            data_source=data_source,
            period=period
        )
        
        if not records:
            logger.warning(f"No data found for {symbol} in range {start_date}-{end_date}")
            raise DataFeedError(f"No data found for {symbol}")
            
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Process 'trade_date' to datetime and set as index
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)
            df.sort_index(ascending=True, inplace=True) # Backtrader needs ascending order
        else:
            raise DataFeedError("Missing 'trade_date' column in historical data")
            
        # Ensure required columns exist and are numeric
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                 # Try to fallback to other names if standard ones missing? 
                 # HistoricalDataService seems to standardize them to open, high, low, close, volume.
                 raise DataFeedError(f"Missing required column '{col}' in historical data")
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Create Feed
        # Note: name parameter helps in identifying the data in cerebro
        data_feed = MongoPandasData(dataname=df, name=symbol)
        
        return data_feed
        
    except Exception as e:
        logger.error(f"Error creating data feed for {symbol}: {e}")
        raise DataFeedError(f"Failed to create data feed: {e}")
