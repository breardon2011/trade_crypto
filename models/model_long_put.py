from app.models.base import OptionsStrategy
from app.services.options_pricing import black_scholes_merton

class LongPut(OptionsStrategy):
    def calculate_profit_loss(self) -> float:
        put_price = black_scholes_merton(
            self.underlying_price, self.strike_price, self.time_to_expiry,
            self.risk_free_rate, self.volatility, 'put'
        )
        return max(self.strike_price - self.underlying_price, 0) - put_price

    def execute_strategy(self) -> dict:
        put_price = black_scholes_merton(
            self.underlying_price, self.strike_price, self.time_to_expiry,
            self.risk_free_rate, self.volatility, 'put'
        )
        return {
            "strategy": "Long Put",
            "put_price": put_price,
            "break_even_point": self.strike_price - put_price,
            "max_loss": put_price,
            "max_profit": "Unlimited (as underlying price approaches 0)"
        }
