import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Imports are now resolved thanks to tests/conftest.py
from src.backend.data_store import DataStore, Base, NewsArticle
from src.backend.exceptions import AppException

TEST_DB_PATH = "test_news.db"

@pytest.fixture(scope="function")
def db_fixture():
    """Fixture to set up and tear down a test database for each test function."""
    # Ensure a clean state before the test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        
    # Use an in-memory database for faster tests, or a file for inspection
    # db_path = ":memory:" 
    db_path = TEST_DB_PATH
    data_store = DataStore(db_path=db_path)
    
    # Yield the DataStore instance to the test function
    yield data_store
    
    # Teardown: Close connection (implicitly handled by SQLAlchemy session scope) 
    # and remove the test database file if it exists
    if os.path.exists(TEST_DB_PATH):
        # Ensure the session is closed before removing the file if needed,
        # though sessionmaker usually handles this.
        # For extra safety: data_store.Session.close_all() 
        os.remove(TEST_DB_PATH)

def create_sample_news(offset_days: int = 0) -> Dict:
    """Helper function to create sample news data."""
    publish_time = datetime.now() - timedelta(days=offset_days)
    return {
        'title': f'Test Title {offset_days}',
        'source': 'Test Source',
        'published_at': publish_time.isoformat(),
        'content': f'Test content for article {offset_days}.',
        'summary': 'Optional summary.',
        'analysis_result': {'sentiment': 'neutral'},
        'keywords': ['test', 'sample', str(offset_days)]
    }

def test_init_db(db_fixture: DataStore):
    """Test if the database and table are created."""
    assert os.path.exists(TEST_DB_PATH) or db_fixture.db_path == "sqlite:///:memory:"
    # Check if the table exists using SQLAlchemy's inspect
    from sqlalchemy import inspect
    inspector = inspect(db_fixture.engine)
    assert NewsArticle.__tablename__ in inspector.get_table_names()

def test_save_news_success(db_fixture: DataStore):
    """Test saving a valid news article."""
    news_data = create_sample_news()
    article_id = db_fixture.save_news(news_data)
    
    assert isinstance(article_id, int)
    assert article_id > 0

    # Verify data was saved correctly
    session = db_fixture.Session()
    try:
        saved_article = session.query(NewsArticle).get(article_id)
        assert saved_article is not None
        assert saved_article.title == news_data['title']
        assert saved_article.source == news_data['source']
        assert saved_article.content == news_data['content']
        assert saved_article.summary == news_data['summary']
        # Compare datetime objects directly after parsing
        assert saved_article.published_at == datetime.fromisoformat(news_data['published_at'])
        assert saved_article.analysis_result == news_data['analysis_result']
        assert saved_article.keywords == news_data['keywords']
    finally:
        session.close()

def test_save_news_missing_field(db_fixture: DataStore):
    """Test saving news with a missing required field."""
    news_data = create_sample_news()
    del news_data['title'] # Remove a required field
    
    with pytest.raises(AppException, match="Missing required field: 'title'"):
        db_fixture.save_news(news_data)

def test_get_news_found(db_fixture: DataStore):
    """Test retrieving an existing news article."""
    news_data = create_sample_news()
    article_id = db_fixture.save_news(news_data)
    
    retrieved_news = db_fixture.get_news(article_id)
    
    assert retrieved_news is not None
    assert isinstance(retrieved_news, dict)
    assert retrieved_news['id'] == article_id
    assert retrieved_news['title'] == news_data['title']
    assert retrieved_news['source'] == news_data['source']
    assert retrieved_news['published_at'] == news_data['published_at'] # Stored as ISO string
    assert retrieved_news['content'] == news_data['content']
    assert retrieved_news['summary'] == news_data['summary']
    assert retrieved_news['analysis_result'] == news_data['analysis_result']
    assert retrieved_news['keywords'] == news_data['keywords']

def test_get_news_not_found(db_fixture: DataStore):
    """Test retrieving a non-existent news article."""
    retrieved_news = db_fixture.get_news(999) # Assuming ID 999 doesn't exist
    assert retrieved_news is None

def test_save_analysis_success(db_fixture: DataStore):
    """Test updating analysis and keywords for an existing article."""
    news_data = create_sample_news()
    article_id = db_fixture.save_news(news_data)
    
    new_analysis = {'sentiment': 'positive', 'score': 0.8}
    new_keywords = ['updated', 'analysis']
    
    db_fixture.save_analysis(article_id, new_analysis, new_keywords)
    
    # Verify the update
    updated_news = db_fixture.get_news(article_id)
    assert updated_news is not None
    assert updated_news['analysis_result'] == new_analysis
    assert updated_news['keywords'] == new_keywords
    # Ensure other fields remain unchanged
    assert updated_news['title'] == news_data['title'] 

def test_save_analysis_not_found(db_fixture: DataStore):
    """Test updating analysis for a non-existent article."""
    new_analysis = {'sentiment': 'negative'}
    new_keywords = ['error']
    
    with pytest.raises(AppException, match="Article with ID 999 not found"):
        db_fixture.save_analysis(999, new_analysis, new_keywords)

def test_get_recent_news(db_fixture: DataStore):
    """Test retrieving recent news articles, checking order and limit."""
    # Save articles with varying publish dates
    article_ids = []
    for i in range(5):
        news_data = create_sample_news(offset_days=i)
        article_ids.append(db_fixture.save_news(news_data))
        
    # Test with limit less than total
    recent_news_limit_3 = db_fixture.get_recent_news(limit=3)
    assert isinstance(recent_news_limit_3, list)
    assert len(recent_news_limit_3) == 3
    # Check descending order by published_at (which corresponds to offset_days=0, 1, 2)
    assert recent_news_limit_3[0]['title'] == 'Test Title 0'
    assert recent_news_limit_3[1]['title'] == 'Test Title 1'
    assert recent_news_limit_3[2]['title'] == 'Test Title 2'
    
    # Test with limit greater than total
    recent_news_limit_10 = db_fixture.get_recent_news(limit=10)
    assert len(recent_news_limit_10) == 5 # Only 5 articles were saved
    assert recent_news_limit_10[0]['title'] == 'Test Title 0'
    assert recent_news_limit_10[4]['title'] == 'Test Title 4'

    # Test default limit (should be 10, but we only have 5)
    recent_news_default = db_fixture.get_recent_news()
    assert len(recent_news_default) == 5

def test_get_recent_news_empty(db_fixture: DataStore):
    """Test retrieving recent news when the database is empty."""
    recent_news = db_fixture.get_recent_news()
    assert isinstance(recent_news, list)
    assert len(recent_news) == 0