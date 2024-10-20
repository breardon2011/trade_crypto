import subprocess
import os
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd


def get_option_expiration_dates(symbol):
    """
    Gets the expiration dates of options for a given symbol.

    Args:
    symbol: Stock symbol

    Returns:
    List of option expiration dates
    """
    ticker = yf.Ticker(symbol)  # Retrieving ticker data
    expirations = ticker.options  # Retrieving option expiration dates
    return expirations

def calculate_implied_volatility(S, K, T, r, price, option_type):
    """
    Calculates the implied volatility using the Black-Scholes model.

    Args:
    S: Current stock price
    K: Option strike price
    T: Time to expiration in years
    r: Risk-free interest rate
    price: Option price
    option_type: 'call' or 'put'

    Returns:
    Implied volatility
    """
    tol = 0.0001  # Tolerance for implied volatility convergence
    max_iter = 100  # Maximum number of iterations

    def black_scholes(option_type, S, K, T, r, sigma):
        """
        Calculates the option price using the Black-Scholes model.
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == 'call':
            option_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            option_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        return option_price

    sigma = 0.5  # Initial guess for implied volatility
    price_est = black_scholes(option_type, S, K, T, r, sigma)  # Initial estimate of option price
    diff = price_est - price  # Difference between estimated price and observed price
    iter_count = 0  # Iteration counter initialization

    while abs(diff) > tol and iter_count < max_iter:
        vega = S * np.sqrt(T) * norm.pdf((np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T)))
        price_est = black_scholes(option_type, S, K, T, r, sigma)  # Estimate of option price
        diff = price_est - price  # New difference between estimated price and observed price

        if abs(diff) < tol:  # Checking for convergence
            break

        sigma = sigma - (diff / vega)  # Updating implied volatility
        iter_count += 1  # Incrementing iteration counter

    return sigma

def calculate_intrinsic_value(S, K, option_type):
    """
    Calculates the intrinsic value of an option.

    Args:
    S: Current stock price
    K: Option strike price
    option_type: 'call' or 'put'

    Returns:
    Intrinsic value
    """
    if option_type == 'call':
        return max(0, S - K)
    else:
        return max(0, K - S)

def calculate_time_value(price, intrinsic_value):
    """
    Calculates the time value of an option.

    Args:
    price: Option price
    intrinsic_value: Intrinsic value of the option

    Returns:
    Time value
    """
    return max(0, price - intrinsic_value)

def calculate_historical_volatility(symbol, start_date, end_date):
    """
    Calculates historical volatility using historical price data.

    Args:
    symbol: Stock symbol
    start_date: Start date for historical data
    end_date: End date for historical data

    Returns:
    Historical volatility
    """
    stock = yf.Ticker(symbol)  # Retrieving stock data
    historical_data = stock.history(start=start_date, end=end_date)  # Retrieving historical data

    # Check if historical data is empty
    if historical_data.empty:
        raise ValueError(f"No historical data found for {symbol} between {start_date} and {end_date}.")

    returns = np.log(historical_data['Close'] / historical_data['Close'].shift(1))  # Calculating log returns
    volatility = returns.std() * np.sqrt(252)  # Calculating historical volatility (252 trading days in a year)
    return volatility


def fetch_option_info(ticker, expiry_date, risk_free_rate):
    """
    Fetches option information for a given ticker, expiry date, and risk-free rate.

    Args:
    ticker: Stock ticker
    expiry_date: Option expiration date
    risk_free_rate: Risk-free interest rate

    Returns:
    Option information
    """
    stock = yf.Ticker(ticker)  # Retrieving stock data
    trade_date = datetime.now()  # Current date
    trade_date = trade_date.replace(tzinfo=None)  # Converting to datetime without timezone

    # Converting expiration date to datetime object and checking if it's valid
    expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').replace(tzinfo=None)
    if expiry_date < trade_date:
        raise ValueError("The specified expiration date has already passed.")

    # Retrieving option chain data
    option_chain = stock.option_chain(expiry_date.strftime('%Y-%m-%d'))
    if option_chain.calls.empty:
        raise ValueError("No call option available for the given ticker and expiry date.")

    # Assuming you're interested in the first available call option
    option = option_chain.calls.iloc[0]
    # Get the most recent stock price
    historical_data = stock.history(period='1d')
    if historical_data.empty:
        raise ValueError(f"No historical data found for {ticker}.")

    underlying_price = historical_data.iloc[-1]['Close']  # Underlying stock price
    strike_price = option['strike']  # Option strike price

    days_to_expiry = (expiry_date - trade_date).days / 365  # Time to expiration in years

    # Calculating implied volatility
    implied_volatility = calculate_implied_volatility(underlying_price, strike_price, days_to_expiry, risk_free_rate, option['lastPrice'], 'call')

    # Calculating intrinsic value for call option
    call_intrinsic_value = calculate_intrinsic_value(underlying_price, strike_price, 'call')

    # Calculating intrinsic value for put option
    put_intrinsic_value = calculate_intrinsic_value(underlying_price, strike_price, 'put')

    # Calculating time value
    time_value = calculate_time_value(option['lastPrice'], call_intrinsic_value)

    return underlying_price, strike_price, days_to_expiry, risk_free_rate, implied_volatility, call_intrinsic_value, put_intrinsic_value, time_value
