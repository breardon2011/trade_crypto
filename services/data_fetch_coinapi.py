import aiohttp
import asyncio
from datetime import timedelta, datetime
import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve the Polygon API key from environment variables
polygon_api_key = os.getenv("POLYGON_API_KEY")
print(f"Using Polygon API Key: {polygon_api_key}")

api_key_coinapi = os.getenv("COIN_MARKET_API_KEY")
print(f"Using CoinAPI Key: {api_key_coinapi}")

market_data_api_key = os.getenv("MARKET_DATA_API_KEY")
print(f"Using Market Data API Key: {market_data_api_key}")


async def get_historical_price(asset_id: str, date: str) -> dict:
    """Get the historical price for a given asset at a specific date."""
    url = f"https://rest.coinapi.io/v1/ohlcv/BITSTAMP_SPOT_{asset_id}_USD/history?period_id=1DAY&time_start={date}T00:00:00&limit=1"
    headers = {'X-CoinAPI-Key': api_key_coinapi}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error: {response.status} - {await response.text()}")
                return None

async def get_option_contracts(asset_id: str, date: str) -> list:
    """Retrieve option contracts data for the given ticker and date from CoinAPI."""
    url = f"https://api.marketdata.app/v1/options/chain/{asset_id}?date={date}"
    headers = {'X-Marke-Key': api_key_coinapi}

    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if 'contracts' in data:
                    return data['contracts']  # Return the list of option contracts
                else:
                    print(f"No data found in response: {data}")
            else:
                print(f"Error: {response.status} - {await response.text()}")
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
    

async def get_intraday_price_at_time(asset_id: str, date: str, time: str) -> float:
    """Retrieve minute-level intraday data for a specific asset and time using CoinAPI."""
    url = f"https://rest.coinapi.io/v1/ohlcv/BITSTAMP_SPOT_{asset_id}_USD/history?period_id=1MIN&time_start={date}T{time}&limit=1"
    headers = {'X-CoinAPI-Key': api_key_coinapi}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    return data[0]['price_close']  # Return close price at this minute
            print(f"Error: {response.status} - {await response.text()}")
    return None


async def main():
    asset_id = "AAPL"
    date = "2024-10-01"
    time = "11:00:00"
    # historical_price = await get_historical_price(asset_id, date)
    # print(historical_price)
    # intraday_price = await get_intraday_price_at_time(asset_id, date, time)
    # print(intraday_price)
    options_contracts = await get_option_contracts(asset_id, date)
    print(options_contracts)


if __name__ == "__main__":
    asyncio.run(main())