from typing import List, Dict, Optional
from loguru import logger

from backend.vector_store import VectorStore

from backend.chain import NewsRAG
from backend.data_store import DataStore
from backend.vector_store import VectorStore
from backend.news_api import NewsAPI
from backend.llm import LLM


def start_news_chain():
    """Analyze fetched news articles"""

    data_store = DataStore()
    vector_store = VectorStore()
    news_api = NewsAPI()
        
    try:
        # Initialize NewsRAG
        news_rag = NewsRAG(
            llm=LLM,
            db=data_store,
            vec_db=vector_store,
            news_api=news_api
        )
        
        news_rag.start()  
        
        logger.info("Successfully analyzed news articles")
    except Exception as e:
        logger.error(f"Failed to analyze news: {str(e)}")
        raise

def get_sources() -> List[Dict]:
    """Get list of available news sources"""
    # TODO: Implement proper source loading from DataStore
    return [
        {"id": "bbc-news", "name": "BBC News"},
        {"id": "cnn", "name": "CNN"},
        {"id": "reuters", "name": "Reuters"}
    ]

def get_articles(
    sources: list[str] = None,
    keywords: str = None,
    from_date: str = None,
    to_date: str = None,
    page: int = 1,
    page_size: int = 10
) -> list[dict]:
    """Get filtered articles from DataStore with pagination"""
    data_store = DataStore()
    return data_store.get_filtered_news(
        sources=sources,
        keywords=keywords,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )

def get_article(article_id: int) -> Optional[dict]:
    """Get a single article by ID from DataStore"""
    data_store = DataStore()
    return data_store.get_news(article_id)