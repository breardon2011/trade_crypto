from app.models.base import OptionsStrategy
from app.services.options_pricing import black_scholes_merton

class LongStraddle(OptionsStrategy):
    def calculate_profit_loss(self) -> float:
        call_price = black_scholes_merton(
            self.underlying_price, self.strike_price, self.time_to_expiry,
            self.risk_free_rate, self.volatility, 'call'
        )
        put_price = black_scholes_merton(
            self.underlying_price, self.strike_price, self.time_to_expiry,
            self.risk_free_rate, self.volatility, 'put'
        )
        total_cost = call_price + put_price
        return self.underlying_price - self.strike_price - total_cost

    def execute_strategy(self) -> dict:
        call_price = black_scholes_merton(
            self.underlying_price, self.strike_price, self.time_to_expiry,
            self.risk_free_rate, self.volatility, 'call'
        )
        put_price = black_scholes_merton(
            self.underlying_price, self.strike_price, self.time_to_expiry,
            self.risk_free_rate, self.volatility, 'put'
        )
        return {
            "strategy": "Long Straddle",
            "call_price": call_price,
            "put_price": put_price,
            "total_cost": call_price + put_price,
            "break_even_points": [
                self.strike_price - (call_price + put_price),
                self.strike_price + (call_price + put_price)
            ]
        }
