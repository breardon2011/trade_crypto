import numpy as np
from scipy.stats import norm

def black_scholes_merton(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option price using Black-Scholes-Merton model.

    Args:
        S (float): Current stock (or asset) price
        K (float): Strike price
        T (float): Time to maturity (in years)
        r (float): Risk-free interest rate
        sigma (float): Volatility of the underlying asset
        option_type (str): 'call' or 'put'

    Returns:
        float: Option price
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:  # put option
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return price
