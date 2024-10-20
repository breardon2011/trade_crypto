from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.long_straddle import LongStraddle
from app.models.long_put import LongPut
from app.services.data_fetcher import fetch_eth_price

router = APIRouter()

class StrategyRequest(BaseModel):
    strategy: str
    strike_price: float
    time_to_expiry: float
    volatility: float

@router.post("/execute_strategy")
async def execute_strategy(request: StrategyRequest):
    eth_price = await fetch_eth_price()
    
    strategy_params = {
        "underlying_price": eth_price,
        "strike_price": request.strike_price,
        "time_to_expiry": request.time_to_expiry,
        "risk_free_rate": 0.01,  # Assume a fixed risk-free rate for simplicity
        "volatility": request.volatility
    }

    if request.strategy == "long_straddle":
        strategy = LongStraddle(**strategy_params)
    elif request.strategy == "long_put":
        strategy = LongPut(**strategy_params)
    else:
        raise HTTPException(status_code=400, detail="Invalid strategy")

    result = strategy.execute_strategy()
    return result
