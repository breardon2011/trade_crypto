import autogen
from dotenv import load_dotenv
import os
from polygon import RESTClient
from tools import fetch_option_info, calculate_implied_volatility
import itertools
from py_vollib.black_scholes.implied_volatility import implied_volatility as bs_iv  # Alias to avoid name clash
from datetime import datetime  # Import datetime for date calculations
from sentiment_alpha import fetch_sentiment_info
from autogen.agentchat.contrib.web_surfer import WebSurferAgent 
import functions

load_dotenv()

open_ai_api_key = os.getenv("OPENAI_API_KEY")
polygon_api_key = os.getenv("POLYGON_API_KEY")

client = RESTClient(api_key=polygon_api_key)
from prompts import Prompts

llm_config = {
    "seed": 42,
    "config_list": [{"model": "gpt-4o", "api_key": open_ai_api_key}]
}

def get_stock_sentiment(ticker):
    # Fetch news sentiment data from Polygon
    sentiment = client.list_ticker_news(ticker, order="desc", limit=10)
    positive = neutral = negative = 0
    breakpoint()
    for article in sentiment:
        if article.sentiment_score > 0.3:
            positive += 1
        elif article.sentiment_score < -0.3:
            negative += 1
        else:
            neutral += 1
    return {"positive": positive, "neutral": neutral, "negative": negative}

def get_alpha_signals(ticker):
    # Fetch additional data for alpha signals
    aggs = client.get_aggs(ticker, 1, "day", limit=30)
    sma_20 = sum(agg.close for agg in aggs[-20:]) / 20
    current_price = aggs[-1].close
    rsi = calculate_rsi(aggs)
    return {
        "price_to_sma_ratio": current_price / sma_20,
        "rsi": rsi,
        "volume_trend": aggs[-1].volume / sum(agg.volume for agg in aggs[-5:]) * 5
    }

def calculate_rsi(aggs, period=14):
    gains = losses = 0
    for i in range(1, period + 1):
        change = aggs[-i].close - aggs[-i-1].close
        if change >= 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / period
    avg_loss = losses / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    return 100 - (100 / (1 + rs))

# Function to calculate implied volatility and option information
def main(ticker: str = 'AAPL', expiry: str = '2024-10-18', date: str = '2019-02-09'):

    implied_volatility = ""
    # Retrieve current price data for the ticker
    current_price_data = client.get_last_trade(ticker)

    # Retrieve quotes for bid/ask prices
    quotes_data = client.list_quotes(ticker, limit=1)
    quotes_list = list(itertools.islice(quotes_data, 20))

    sentiment=fetch_sentiment_info(ticker,date)
    # Check if there are any quotes available
    if quotes_list:
        latest_quote = quotes_list[0]
        bid_price = latest_quote.bid_price
        ask_price = latest_quote.ask_price
        bid_ask_spread = ask_price - bid_price
        market_price = (bid_price + ask_price) / 2  # Using mid price as market price
    else:
        bid_price = ask_price = bid_ask_spread = market_price = None
        print("No bid/ask quotes available for this ticker.")
        return

    # Retrieve options chain for the ticker and expiration date
    try:
        options_data = client.list_options_contracts(underlying_ticker=ticker, expiration_date=expiry)

        # Limit to the first 10 options for inspection to prevent freezing
        limited_options = list(itertools.islice(options_data, 20))

        if limited_options:
            first_option = limited_options[0]
            strike_price = first_option.strike_price
        

            # Use today's date to calculate days to expiry
            today = datetime.today()
            expiration_date = datetime.strptime(expiry, "%Y-%m-%d")
            days_to_expiry = (expiration_date - today).days
        else:
            strike_price = days_to_expiry = None
            print("No options data available for this ticker and expiration date.")
            return
    except Exception as e:
        print(f"An error occurred while fetching options data: {e}")
        return

    # Define the Black-Scholes parameters
    S = current_price_data.price  # Current underlying price
    K = strike_price  # Strike price of the option
    T = days_to_expiry / 365  # Time to expiration in years
    r = 0.0398  # Risk-free interest rate
    option_type = 'c'  # 'c' for call, 'p' for put (can be adjusted based on the option type)


    implied_volatility = functions.analyze_iron_condor_setup(ticker)
    contract_data = functions.test() 

    
    start_date = "2019-01-01"
    end_date = "2019-02-09"

    split_multiplier = 4

# Fetch daily aggregated data for the given date range
    aggs = client.get_aggs(ticker, multiplier=1, timespan="day", from_=start_date, to=end_date)

# Create a new list to hold the adjusted price data
    adjusted_aggs = []

# Process each aggregation entry and adjust prices
    for agg in aggs:
    # Multiply OHLC prices by the split multiplier
        # breakpoint()
        adjusted_agg = {
            "date": datetime.utcfromtimestamp(agg.timestamp / 1000).strftime('%Y-%m-%d'),
            "open": agg.open * split_multiplier,
            "high": agg.high * split_multiplier,
            "low": agg.low * split_multiplier,
            "close": agg.close * split_multiplier,
            "volume": agg.volume,
        }
    # Add the adjusted entry to the new list
        adjusted_aggs.append(adjusted_agg)
    # Calculate implied volatility
    # try:
    #     breakpoint()
    #     implied_volatility = bs_iv(market_price, S, K, T, r, option_type)
    #     print(f"Implied Volatility: {iv:.4f}")
    # except Exception as e:
    #     print(f"An error occurred while calculating implied volatility: {e}")
    #     iv = None

        # Get stock sentiment
    # sentiment = get_stock_sentiment(ticker)

    # # Get alpha signals
    # alpha_signals = get_alpha_signals(ticker)

    # Create the context dictionary
    option_context = {
        "ticker": ticker,
        "last_price": S,
        "bid_price": bid_price,
        "ask_price": ask_price,
        "bid_ask_spread": bid_ask_spread,
        "contract_data": contract_data,
        "sentiment": sentiment,
        # "alpha_signals": alpha_signals

    }
        # Convert the option context to a formatted string for the agent to understand
    context_str = f"""
        Ticker: {option_context['ticker']}
        Contract Data : {option_context['contract_data']}
        Aggregated History: {adjusted_aggs}
        

    """



    # Continue with the autogen integration using the created option_context
    user_proxy = autogen.AssistantAgent(
        name="user_proxy",
        llm_config=llm_config,
        description="User proxy agent",
        system_message="user_proxy",
    )

    planner = autogen.AssistantAgent(
        name="Planner",
        llm_config=llm_config,
        description="Planner agent for trade analysis", 
        system_message=f"{Prompts.planner_prompt()}"
    )

    # Add context to Stock Analyst using system message
    engineer = autogen.AssistantAgent(
        name="StockAnalyst",
        llm_config=llm_config,
        description="Stock Analyst specialized in option trading strategies",
        system_message=f"{Prompts.analyst_prompt()}\nHere is the context information for analysis:\n{context_str}"
    )

    critic = autogen.AssistantAgent(
        name="Critic",
        llm_config=llm_config,
        description="Critic to evaluate the stock analysis provided. . ",  
        system_message=f"{Prompts.critic_prompt()}- {Prompts.iron()}Ensure that the spread would currently be in the money \nHere is the context information:\n{context_str}"
    )

#     web_surfer = WebSurferAgent(
#     "web_surfer",
#     llm_config=llm_config,
#     summarizer_llm_config=llm_config,
#     is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
#     browser=browser,
# )

    # scientist = autogen.AssistantAgent(
    #     name="Scientist",
    #     llm_config=llm_config,
    #     description="Scientist for exploring alternative evaluation methods", 
    #     system_message=f"You are the iron condor expert. Help evaluate proposed spreads.Here is information: {Prompts.iron()}\nHere is the context:\n{context_str}"
    # )

    group_chat = autogen.GroupChat(
        agents=[user_proxy, engineer, critic, planner],
        messages=[],
        max_round=12,
    )

    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)
    user_proxy.initiate_chat(recipient=manager, message="Analyze the provided ticker to recommend an Iron Condor options buy")


main()
