import aiohttp
import asyncio
from datetime import timedelta, datetime
import os
import pytz
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Retrieve the Polygon API key from environment variables
polygon_api_key = os.getenv("POLYGON_API_KEY")
print(f"Using Polygon API Key: {polygon_api_key}")

api_key_coinapi = os.getenv("COIN_MARKET_API_KEY")
print(f"Using CoinAPI Key: {api_key_coinapi}")

market_data_api_key = os.getenv("MARKET_DATA_API_KEY")
print(f"Using Market Data API Key: {market_data_api_key}")

def rename_market_data(data):
    """Process the data to include dates with each quote."""
    if all(key in data for key in ['o', 'h', 'l', 'c', 'v']):
        market_data = []    
        for i in range(len(data['t'])):
            market_data.append({
                'date': datetime.fromtimestamp(data['t'][i], tz=pytz.utc).strftime('%Y-%m-%d'),
                'time': datetime.fromtimestamp(data['t'][i], tz=pytz.utc).strftime('%H:%M'),
                'open': data['o'][i],
                'high': data['h'][i],
                'low': data['l'][i],
                'close': data['c'][i],
                'volume': data['v'][i]
            })
    return market_data


async def get_historical_price(asset_id: str, date_from: str, date_to: str) -> dict:
    """Get the historical price for a given asset at a specific date from the Market Data API."""
    url = f"https://api.marketdata.app/v1/stocks/candles/D/{asset_id}/?from={date_from}&to={date_to}"
    headers = {'Authorization': f'Bearer {market_data_api_key}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status in [200, 203]:
                data = await response.json()
                # Process the data to include dates with each quote
                historical_data = rename_market_data(data)
                return historical_data
            else:
                print(f"Error: {response.status} - {await response.text()}")
                return None

async def get_option_contracts(asset_id: str) -> None:
    """Retrieve option contracts data for the given ticker from Market Data API and print each contract as an individual JSON record."""
    url = f"https://api.marketdata.app/v1/options/chain/{asset_id}/"
    headers = {'Authorization': f'Bearer {market_data_api_key}'}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status in [200, 203]:
                data = await response.json()
                if data['s'] == 'ok':
                    return data
                else:
                    print(f"No data found in response: {data}")
            else:
                print(f"Error: {response.status} - {await response.text()}")


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
    

async def get_intraday_price_at_time(asset_id: str, date: str) -> float:
    """Retrieve minute-level intraday data for a specific asset and time using Market Data API."""
    url = f"https://api.marketdata.app/v1/stocks/candles/1/{asset_id}/?date={date}T11%3A00%3A00-07%3A00"
    
    headers = {'Authorization': f'Bearer {market_data_api_key}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status in [200, 203]:
                data = await response.json()
               # Process the data to include dates with each quote
                intraday_data = rename_market_data(data)
                return intraday_data

            print(f"Error fetching intraday price: {response.status} - {await response.text()}")
    return None


async def main():
    ticker = "AAPL"
    date_from = "2024-10-01"
    date_to = "2024-10-04"
    time = "11:00:00"
   
    # historical_price = await get_historical_price(asset_id, date_from, date_to)
    # print('Historical Price NEW:')
    # print(json.dumps(historical_price, indent=4))  # Pretty print the historical price
    
    intraday_price = await get_intraday_price_at_time(asset_id=ticker, date=date_from)
    print('Intraday Price NEW:')
    print(json.dumps(intraday_price, indent=4))  # Pretty print the intraday price
   
    # options_contracts = await get_option_contracts(asset_id)
    # print('Options Contracts NEW:')
    # print(json.dumps(options_contracts, indent=4))  # Pretty print the options contracts


if __name__ == "__main__":
    asyncio.run(main())
