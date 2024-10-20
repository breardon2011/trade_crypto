import aiohttp
from app.core.config import settings

async def fetch_coinbase_price(asset_id: str) -> float:
    url = f"https://api.coinbase.com/v2/prices/{asset_id}/spot"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return float(data['data']['amount'])

async def fetch_coinbase_historical_data(asset_id: str, start: str, end: str) -> dict:
    url = f"https://api.coinbase.com/v2/prices/{asset_id}/historic?start={start}&end={end}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()