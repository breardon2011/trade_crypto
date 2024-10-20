import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv() 
alpha_v_api_key = os.getenv("ALPHAVANTAGE_API_KEY")

def get_sentiment_analysis(symbol, time_from, time_to):
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&time_from={time_from}&time_to={time_to}&apikey={alpha_v_api_key}'
    response = requests.get(url)
    data = response.json()
    return data

def calculate_sentiment_score(sentiment_data):
    articles = sentiment_data.get('feed', [])
    if not articles:
        return None  # No articles available

    total_score = 0
    article_count = len(articles)

    for article in articles:
        sentiment = article.get('overall_sentiment_score', 0)  # Example field
        total_score += sentiment

    return total_score / article_count if article_count > 0 else None

def fetch_sentiment_info(symbol,date):
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    one_year_ago = date_obj - timedelta(days=365)

    time_from = one_year_ago.strftime("%Y%m%dT%H%M")
    time_to = date_obj.strftime("%Y%m%dT%H%M")

    # Fetch sentiment data with the time range
    sentiment_data = get_sentiment_analysis(symbol, time_from, time_to)
    sentiment_score = calculate_sentiment_score(sentiment_data)
    
    return sentiment_score
