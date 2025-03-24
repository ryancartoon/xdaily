from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .exceptions import AppException

Base = declarative_base()


class NewsArticle(Base):
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=True)
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=False)
    published_at = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(Text)
    analysis_result = Column(JSON)
    keywords = Column(JSON)


class NewsSource(Base):
    __tablename__ = 'news_sources'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=True)
    source = Column(String(255), nullable=False, unique=True)

    

class DataStore:
    def __init__(self, db_path: str = "news.db"):
        """
        Initialize the DataStore with a SQLite database connection.

        Args:
            db_path: Path to the SQLite database file (default: "news.db")
        """
        self.db_path = f"sqlite:///{db_path}"
        self.engine = create_engine(self.db_path)
        self.Session = sessionmaker(bind=self.engine)
        self._init_db()

    def _init_db(self):
        """
        Initialize the database by creating all tables defined in the SQLAlchemy models.
        This is called automatically during initialization.
        """
        Base.metadata.create_all(self.engine)

    def save_news(self, news_data: dict) -> int:
        """Save a news article using SQLAlchemy ORM
        Args:
            news_data: Dictionary containing news article data with keys:
                - title (str)
                - source (str)
                - published_at (str in ISO format)
                - content (str)
                - summary (str, optional)
                - analysis_result (str, optional)
                - keywords (str, optional)

        Returns:
            int: ID of the saved article
        """
        session = self.Session()

        article = NewsArticle(
            title=news_data['title'],
            source=news_data['source'],
            published_at=datetime.fromisoformat(news_data['published_at']),
            content=news_data['content'],
            summary=news_data.get('summary'),
            analysis_result=news_data.get('analysis_result'),
            keywords=news_data.get('keywords'),
            url=news_data.get("url"),
        )

        try:
            session.add(article)
            session.flush()
            session.commit()

            return article.id

        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            session.rollback()
            raise AppException(f"Failed to save news: {str(e)}")
        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            session.rollback()
            raise AppException(f"Missing required field: {str(e)}")
        finally:
            session.close()
    
    def save_analysis(self, id: int, analysis: str, keywords: List[str]) -> None:
        """Update analysis results and keywords for a news article by ID
        
        Args:
            id: Article ID to update
            analysis: Analysis text to save
            keywords: List of keywords to save (will be stored as JSON)
            
        Raises:
            AppException: If database operation fails or article not found
        """
        session = self.Session()
        try:
            article = session.query(NewsArticle).get(id)
            if not article:
                raise AppException(f"Article with ID {id} not found")
            
            article.analysis_result = analysis
            article.keywords = keywords
            session.commit()

        except SQLAlchemyError as e:
            logger.error(f"Database error during update: {str(e)}")
            session.rollback()
            raise AppException(f"Failed to save analysis: {str(e)}")
        finally:
            session.close()

    def get_news(self, news_id: int) -> Optional[Dict]:
        """
        Retrieve a single news article by its ID.

        Args:
            news_id: The ID of the article to retrieve

        Returns:
            Dict if found, None otherwise

        Raises:
            AppException: If there's a database error
        """
        session = self.Session()

        try:
            article = session.query(NewsArticle).filter_by(id=news_id).first()
            if not article:
                return None
                
            data = {
                'id': article.id,
                'title': article.title,
                'source': article.source,
                'published_at': article.published_at.isoformat(),
                'content': article.content,
                'summary': article.summary,
                'analysis_result': article.analysis_result,
                'keywords': article.keywords,
            }
            return data
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise AppException(f"Failed to get news: {str(e)}")
        finally:
            session.close()

    def get_recent_news(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve the most recent news articles, ordered by publication date.

        Args:
            limit: Maximum number of articles to return (default: 10)

        Returns:
            List of Dict

        Raises:
            AppException: If there's a database error
        """
        session = self.Session()
        try:
            articles = session.query(NewsArticle)\
                .order_by(NewsArticle.published_at.desc())\
                .limit(limit)\
                .all()
                
            documents = []
            for article in articles:
                data = {
                    'id': article.id,
                    'title': article.title,
                    'source': article.source,
                    'published_at': article.published_at.isoformat(),
                    'content': article.content,
                    'summary': article.summary,
                    'analysis_result': article.analysis_result,
                    'keywords': article.keywords,
                }
                documents.append(data)
            return documents
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise AppException(f"Failed to get recent news: {str(e)}")
        finally:
            session.close()

    def get_filtered_news(
        self,
        sources: List[str] = None,
        keywords: str = None,
        from_date: str = None,
        to_date: str = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Dict]:
        """
        Retrieve filtered and paginated news articles from database.
        
        Args:
            sources: List of source names to filter by
            keywords: Text to search in title/content
            from_date: Minimum publish date (ISO format string)
            to_date: Maximum publish date (ISO format string)
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            List of article dictionaries
            
        Raises:
            AppException: If database error occurs
        """
        session = self.Session()
        try:
            query = session.query(NewsArticle)
            
            # Apply filters
            if sources:
                query = query.filter(NewsArticle.source.in_(sources))
            if from_date:
                query = query.filter(NewsArticle.published_at >= datetime.fromisoformat(from_date))
            if to_date:
                query = query.filter(NewsArticle.published_at <= datetime.fromisoformat(to_date))
            if keywords:
                keywords = f"%{keywords.lower()}%"
                query = query.filter(
                    (NewsArticle.title.ilike(keywords)) |
                    (NewsArticle.content.ilike(keywords))
                )
            
            # Apply pagination
            offset = (page - 1) * page_size
            articles = query.order_by(NewsArticle.published_at.desc())\
                            .offset(offset)\
                            .limit(page_size)\
                            .all()
            
            # Convert to dict format
            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'title': article.title,
                    'source': {'name': article.source},
                    'published_at': article.published_at.isoformat(),
                    'content': article.content,
                    'summary': article.summary,
                    'analysis_result': article.analysis_result,
                    'keywords': article.keywords,
                })
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise AppException(f"Failed to get filtered news: {str(e)}")
        finally:
            session.close()

    def get_sources(self) -> List[Dict]:
        """Get list of all news sources from dedicated table"""
        session = self.Session()
        try:
            sources = session.query(NewsSource).all()
            return [{'name': s.source} for s in sources]
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise AppException(f"Failed to get sources: {str(e)}")
        finally:
            session.close()