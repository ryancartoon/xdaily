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
            'page_size': 3,
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

        # news = [
        #     {
        #         'source': 'bbc-news',
        #         'author': 'BBC News',
        #         'title': "Kilmar Abrego Garcia: Sen Van Hollen says deported man 'traumatised'",
        #         'description': 'Sen Chris Van Hollen returned from El Salvador and spoke about his time meeting with Kilmar Ábrego García.',
        #         'url': 'https://www.bbc.co.uk/news/articles/cjdx0gp0kd0o',
        #         'urlToImage': 'https://ichef.bbci.co.uk/ace/branded_news/1200/cpsprodpb/32c2/live/70aee0e0-1cb6-11f0-8a1e-3ff815141b98.jpg',
        #         'published_at': '2025-04-19T03:37:22.8953419Z',
        #         'content': 'President Donald Trump told reporters at the White House Mr Ábrego García was "not a very innocent guy".\r\nMr Ábrego García has faced at least two other allegations of criminal activity, '
        #     },
        #     # {
        #     #     'source': 'bbc-news',
        #     #     'author': 'BBC News',
        #     #     'title': 'Influencers fuelling misogyny in schools, teachers say',
        #     #     'description': 'Almost three in five teachers believe social media use has had a negative effect on behaviour in schools, according to a union poll.',
        #     #     'url': 'https://www.bbc.co.uk/news/articles/crm3x92mpdxo',
        #     #     'urlToImage': 'https://ichef.bbci.co.uk/ace/branded_news/1200/cpsprodpb/9027/live/b4598050-1cb8-11f0-a3a8-a5e49d306c01.jpg',
        #     #     'published_at': '2025-04-19T03:37:20.6146597Z',
        #     #     'content': 'Union members will debate motions at its annual conference in Liverpool this weekend, including one that suggests far-right and populist movements have shifted their recruitment on to social media,'
        #     # },
        #     # {
        #     #     'source': 'bbc-news',
        #     #     'author': 'BBC News',
        #     #     'title': 'Anxiety on US college campuses as foreign students deported',
        #     #     'description': 'High-profile detentions and visa revocations are putting students on edge, as Trump tightens his squeeze on US schools.',
        #     #     'url': 'https://www.bbc.co.uk/news/articles/c20xq5nd8jeo',
        #     #     'urlToImage': 'https://ichef.bbci.co.uk/ace/branded_news/1200/cpsprodpb/b21a/live/723549e0-1ca2-11f0-a455-cf1d5f751d2f.jpg',
        #     #     'published_at': '2025-04-19T00:22:19.8659081Z',
        #     #     'content': 'For the last few weeks, many foreign students living in the US have watched as a sequence of events has repeated itself on their social media feeds: plain-clothes agents appearing unannounced and hau… [+1797 chars]'
        #     # }
        # ]

        return articles

    # def fetch_everything(self, query: str) -> List[NewsDocument]:
    #     """Fetch all news articles matching the query from the last specified hours"""
    #     """
    #     :param from_param: A date and optional time for the oldest article allowed.
    #         If a str, the format must conform to ISO-8601 specifically as one of either
    #         ``%Y-%m-%d`` (e.g. *2019-09-07*) or ``%Y-%m-%dT%H:%M:%S`` (e.g. *2019-09-07T13:04:15*).
    #         An int or float is assumed to represent a Unix timestamp.  All datetime inputs are assumed to be UTC.
    #     :type from_param: str or datetime.datetime or datetime.date or int or float or None

    #     :param to: A date and optional time for the newest article allowed.
    #         If a str, the format must conform to ISO-8601 specifically as one of either
    #         ``%Y-%m-%d`` (e.g. *2019-09-07*) or ``%Y-%m-%dT%H:%M:%S`` (e.g. *2019-09-07T13:04:15*).
    #         An int or float is assumed to represent a Unix timestamp.  All datetime inputs are assumed to be UTC.
    #     :type to: str or datetime.datetime or datetime.date or int or float or None
    #     """
    #     try:
    #         # from_date = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d')
            
    #         params = {
    #             'q': query,
    #             'language': 'en',
    #             'page_size': 50,
    #             # 'from_': from_date,
    #             'sort_by': 'publishedAt'
    #         }
            
    #         logger.debug(f"Fetching news with params: {params}")
    #         response = self.client.get_everything(**params)
            
    #         if response['status'] != 'ok':
    #             raise APIError(f"NewsAPI returned error: {response.get('message', 'Unknown error')}")
            
    #         documents = []
    #         for article in response['articles']:
    #             doc = self._convert_article_to_news_document(article)
    #             documents.append(doc)
            
    #         logger.info(f"Successfully fetched {len(documents)} news articles for query: {query}")
    #         return documents
            
    #     except Exception as e:
    #         logger.error(f"Failed to fetch news: {str(e)}")
    #         raise APIError("Failed to fetch news") from e 