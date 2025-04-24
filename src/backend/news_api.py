from newsapi import NewsApiClient
from typing import List, Dict
from loguru import logger
from datetime import datetime, timedelta

from config.settings import settings
from backend.exceptions import APIError


class NewsAPI:
    def __init__(self):
        self.client = NewsApiClient(api_key=settings.NEWSAPI_KEY)
        # 'sources': 'bbc-news,the-associated-press,al-jazeera-english,the-wall-street-journal,the-washington-post',
        self.sources = 'bbc-news'
        
    def get_top_headlines(self) -> List[Dict]:
        """Fetch top headlines from the last specified hours"""
        # Calculate the date from hours ago
        
        params = {
            'sources': self.sources,
            'language': 'en',
            'page_size': 10,
        }
        
        logger.debug(f"Fetching news with params: {params}")
        response = self.client.get_top_headlines(**params)
        
        if response['status'] != 'ok':
            raise APIError(f"NewsAPI returned error: {response.get('message', 'Unknown error')}")
        
        articles = response['articles']
        logger.info(f"Successfully fetched {len(articles)} news articles")

        for article in articles:
            article["published_at"] = article.pop("publishedAt")
            article["source"] = article["source"]["id"]

        return articles
