from abc import ABC, abstractmethod
from pydantic import BaseModel

class OptionsStrategy(ABC, BaseModel):
    underlying_price: float
    strike_price: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float

    @abstractmethod
    def calculate_profit_loss(self) -> float:
        pass

    @abstractmethod
    def execute_strategy(self) -> dict:
        pass
