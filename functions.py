import requests
from datetime import timedelta, datetime
import pytz
from dotenv import load_dotenv
import os
from scipy import optimize
from scipy.stats import norm
import os
from math import log, sqrt, exp
import json

# Load environment variables
load_dotenv()

# Retrieve the Polygon API key from environment variables
polygon_api_key = os.getenv("POLYGON_API_KEY")
print(f"Using Polygon API Key: {polygon_api_key}")


def get_historical_price(ticker, date):
    """Get the historical price for a given ticker at a specific date and time."""
    url = f"https://api.polygon.io/v1/open-close/{ticker}/{date}?adjusted=true&apiKey={polygon_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    

def get_past_monday(target_date):
    """Calculate the date of the most recent Monday relative to a target date."""
    days_since_monday = target_date.weekday()  # Monday is 0, Sunday is 6
    past_monday = target_date - timedelta(days=days_since_monday)
    return past_monday


def get_next_friday(start_date):
    """Calculate the next Friday after the given date."""
    next_friday = start_date + timedelta((4 - start_date.weekday()) % 7)
    return next_friday


def get_day():
    """Calculate the target dates (past Monday at 11:00 AM and next Friday)."""
    today = datetime.now(pytz.timezone("US/Eastern"))
    one_month_ago = today - timedelta(days=60)  # Avoid Labor Day
    past_monday = get_past_monday(one_month_ago)

    # Calculate the next Friday
    next_friday = get_next_friday(past_monday)
    print(f"Past Monday: {past_monday.strftime('%Y-%m-%d')}, Next Friday: {next_friday.strftime('%Y-%m-%d')}")
    expiration = next_friday.strftime('%Y-%m-%d')
    monday = past_monday.strftime('%Y-%m-%d')

    # Define the date and time of 11:00 AM EST on that past Monday
    past_monday_11am = past_monday.replace(hour=11, minute=0, second=0, microsecond=0)

    # Convert to UTC (Polygon API uses UTC timestamps)
    utc_past_monday_11am = past_monday_11am.astimezone(pytz.utc)
    utc_past_monday_11am_str = utc_past_monday_11am.strftime('%Y-%m-%dT%H:%M:%SZ')

    return utc_past_monday_11am_str, expiration, monday


def get_historical_price(ticker, date):
    """Get the historical price for a given ticker at a specific date and time."""
    url = f"https://api.polygon.io/v1/open-close/{ticker}/{date}?adjusted=true&apiKey={polygon_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    

def get_intraday_price_at_time(ticker, date, time):
    """Retrieve minute-level intraday data for a specific ticker and time."""
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{date}/{date}?adjusted=true&apiKey={polygon_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('results', [])
        for bar in data:
            timestamp = datetime.fromtimestamp(bar['t'] / 1000, tz=pytz.utc)  # Convert to datetime
            if timestamp.time() == time:  # Match the specific time
                return bar['c']  # Return close price at this minute
    return None


# Define the function to get historical option data from Dolthub
def get_option_contracts_from_dolthub(ticker, date):
    """Retrieve AAPL option contracts data from Dolthub for the given date."""
    # Construct the query to get options data for a specific ticker and date
   # query = f"SELECT * FROM `option_chain` WHERE act_symbol='{ticker}' AND date='{date}'"
    # url = f"{dolthub_url}?q={query}"

    response = requests.get('https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master?q=SELECT+*+FROM+%60option_chain%60+WHERE+act_symbol=%27AAPL%27+AND+date=%272019-02-09%27')
    if response.status_code == 200:
        data = response.json()
        if 'rows' in data:
            return data['rows']  # Return the list of rows containing option contracts
        else:
            print(f"No data found in response: {data}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return None

# Modify the function to use Dolthub data for a specific date
def get_option_contracts_for_day(ticker, date):
    """Retrieve all available option contracts for the given ticker and date using Dolthub."""
    return get_option_contracts_from_dolthub(ticker, date)



def get_option_contracts_for_day_old(ticker, date):
    """Retrieve all available option contracts for the given ticker and date, handling pagination."""
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&expiration_date={date}&expired=True&apiKey={polygon_api_key}"
    all_contracts = []
    
    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            contracts = data.get('results', [])
            all_contracts.extend(contracts)  # Add current page contracts to the list

            # Check if there is a next URL for pagination
            url = data.get('next_url')
            
            if url:
                print(f"Fetching next page: {url}")
                url = url + "&apiKey=" + polygon_api_key
            else:
                break
        else:
            print(f"Error fetching option contracts: {response.status_code} - {response.text}")
            break

    return all_contracts


def calculate_strike_intervals(contracts):
    """Calculate the strike price intervals from the available contracts."""
    try:
        # Extract unique sorted strike prices from contracts
        strike_prices = sorted(set(float(contract['strike']) for contract in contracts if 'strike' in contract))
        
        # Log the extracted strike prices for debugging
        print(f"Extracted strike prices: {strike_prices}")
        
        # Calculate intervals between consecutive strike prices
        intervals = [strike_prices[i + 1] - strike_prices[i] for i in range(len(strike_prices) - 1)]
        
        # Log the calculated intervals for debugging
        print(f"Calculated intervals: {intervals}")

        # Return the most common interval (or minimum interval as default)
        return min(intervals) if intervals else None

    except Exception as e:
        print(f"An error occurred while calculating strike intervals: {e}")
        return None
    
# Define the Black-Scholes model to calculate the option price
def black_scholes_price(S, K, T, r, sigma, option_type="call"):
    """Calculate the price of a European option using the Black-Scholes formula.
    :param S: Current stock price
    :param K: Option strike price
    :param T: Time to expiration in years
    :param r: Risk-free interest rate
    :param sigma: Implied volatility
    :param option_type: 'call' or 'put'
    :return: Theoretical option price
    """
    d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if option_type == "call":
        return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    elif option_type == "put":
        return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

# Define a function to solve for implied volatility
def implied_volatility(market_price, S, K, T, r, option_type="call"):
    """Calculate implied volatility using the Black-Scholes formula.
    :param market_price: Observed market price of the option
    :param S: Current stock price
    :param K: Option strike price
    :param T: Time to expiration in years
    :param r: Risk-free interest rate
    :param option_type: 'call' or 'put'
    :return: Implied volatility as a float
    """

    S = S * 4 #AAPL split 4 to 1 in 2020, polygon prices reflect adjusted

    # Ensure inputs are valid
    # if market_price <= 0 or S <= 0 or K <= 0 or T <= 0:
    #     print(f"Invalid inputs for IV calculation: market_price={market_price}, S={S}, K={K}, T={T}")
    #     return None
    # Objective function for optimization (difference between market and theoretical price)
    objective_function = lambda sigma: market_price - black_scholes_price(S, K, T, r, sigma, option_type)
    
    # Use a numerical solver to find the IV, starting with a reasonable range
    try:
        # Adjust the bracket range if needed based on the observed data
        result = optimize.root_scalar(objective_function, bracket=[0.001, 3.0], method='brentq')
        return result.root if result.converged else None
    except ValueError as e:
        print(f"Failed to find IV for {option_type} option with strike {K} and market price {market_price}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return None

def filter_contracts(contracts, current_price, expiration_date, width):
    """Filter contracts to select the best candidates for an iron condor."""
    filtered = []
    for contract in contracts:
        if contract['expiration_date'] == expiration_date:
            strike_price = float(contract['strike_price'])
            if (contract['contract_type'] == 'put' and
                current_price - 2 * width < strike_price < current_price - width) or \
               (contract['contract_type'] == 'call' and
                current_price + width < strike_price < current_price + 2 * width):
                filtered.append(contract)
    return filtered

# Calculate implied volatility for each of the filtered contracts
# Calculate implied volatility for each of the filtered contracts
def calculate_iv_for_contracts(contracts, current_price):
    """Calculate implied volatility for each contract in the list.
    
    :param contracts: List of option contracts retrieved from Dolthub.
    :param current_price: The current price of the underlying asset.
    :return: A list of contracts with their respective implied volatilities.
    """
    # Risk-free rate (e.g., use the current yield on a 1-month US Treasury bond)
    risk_free_rate = 0.0398  # Example fixed risk-free rate; adjust as needed
    
    # Set the reference date to February 9, 2019
    reference_date = datetime(2019, 2, 9, tzinfo=pytz.utc)  # Use February 9, 2019 in UTC

    # Calculate IV for each contract
    contracts_with_iv = []
    for contract in contracts:
        strike_price = float(contract['strike'])  # Use 'strike' from the contract
        option_type = contract['call_put'].lower()  # Determine if it's a call or put

        # Use the expiration date from the contract to calculate time to expiration (T)
        expiration_date = contract['expiration']
        expiration_date_dt = datetime.strptime(expiration_date, "%Y-%m-%d").replace(tzinfo=pytz.utc)  # Make expiration_date UTC aware

        # Calculate time to expiration in years, using reference date instead of current date
        T = (expiration_date_dt - reference_date).days / 365.0

        # Use the 'ask' price as the market price if available, otherwise skip
        market_price = float(contract.get('ask', 0))
        if market_price > 0 and strike_price > 0:
            # Calculate implied volatility using the Black-Scholes model
            iv = implied_volatility(market_price, current_price, strike_price, T, risk_free_rate, option_type)
            if iv is not None:
                # Add the IV to the contract details
                contract_with_iv = {**contract, 'implied_volatility': iv}
                contracts_with_iv.append(contract_with_iv)
                print(f"Calculated IV for {option_type} option with strike {strike_price} and expiration {expiration_date}: {iv:.4f}")
        else:
            print(f"Skipping contract due to missing or invalid market/strike price: {contract}")

    return contracts_with_iv



def analyze_iron_condor_setup(ticker):
    """Analyze the iron condor setup for a given ticker on February 9, 2019."""
    # Set the specific date for analysis: February 9, 2019
    monday = "2019-02-08"
    
    
    # Get the historical price of the underlying asset at 11:00 AM EST on February 9, 2019
    intraday_price = get_intraday_price_at_time(ticker, monday, datetime(2019, 2, 8, 16, 0, tzinfo=pytz.utc).time())  # 11:00 AM EST is 16:00 UTC
    if not intraday_price:
        print(f"Could not retrieve intraday price for {ticker} on {monday} at 11:00 AM EST.")
        return None
    

    
    print(f"Underlying price at 11:00 AM EST on {monday}: {intraday_price}")
    
    # Get all option contracts for the given expiration date from Dolthub
    contracts = get_option_contracts_for_day(ticker, "2019-02-09")
    if not contracts:
        print(f"No option contracts found for {ticker} on {monday}.")
        return None
    
    # Calculate the strike price intervals from the available contracts
    interval = calculate_strike_intervals(contracts)
    if not interval:
        print("Unable to determine the strike price interval.")
        return None

    print(f"Calculated strike price interval: {interval}")

 
    


    # Return the filtered contracts for further analysis or IV calculation
    iv = calculate_iv_for_contracts(contracts, intraday_price)
    return iv

# Test the function to ensure everything is working
def test():
    return analyze_iron_condor_setup("AAPL")

# test()


# # TESTING 
# historical_price = get_historical_price("AAPL", "2024-10-01")
# print('Historical Price FUNCTIONS:')
# print(json.dumps(historical_price, indent=4))  # Pretty print the JSON

# options_contracts = get_option_contracts_from_dolthub("AAPL", "2024-10-01")
# print('Options Contracts FUNCTIONS:')
# print(json.dumps(options_contracts, indent=4))  # Pretty print the JSON

intraday_price = get_intraday_price_at_time("AAPL", "2024-10-01", "11:00:00")
print('Intraday Price FUNCTIONS:')
print(json.dumps(intraday_price, indent=4))  # Pretty print the JSON