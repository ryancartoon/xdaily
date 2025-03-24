import pytest
import os
import shutil
import time
from typing import List
from langchain_core.documents import Document
from src.backend.vector_store import VectorStore
from loguru import logger

TEST_DB_PATH = "test_chroma_db"

def remove_test_db(path, retries=5, delay=0.5):
    """Helper function to robustly remove the test database directory."""
    for i in range(retries):
        if not os.path.exists(path):
            return
        try:
            shutil.rmtree(path)
            time.sleep(0.1) # Small delay after successful removal
            return
        except OSError as e:
            logger.warning(f"Attempt {i+1} to remove {path} failed: {e}")
            time.sleep(delay)
    logger.error(f"Failed to remove {path} after {retries} retries.")
    # If removal still fails, try a less aggressive cleanup or just log and continue
    if os.path.exists(path):
         logger.error(f"Directory {path} still exists after cleanup attempts.")


@pytest.fixture(scope="function")
def vector_store_fixture():
    """Fixture to set up and tear down a test vector store for each test function."""
    # Clean up test DB if it exists
    remove_test_db(TEST_DB_PATH)
    
    # Ensure directory exists with proper permissions
    os.makedirs(TEST_DB_PATH, mode=0o777, exist_ok=True)
    
    # Create VectorStore instance
    vector_store = VectorStore(persist_directory=TEST_DB_PATH)
    
    yield vector_store
    
    # Teardown - remove test DB
    # Explicitly delete client to help with garbage collection
    try:
        del vector_store.client
    except Exception as e:
        logger.warning(f"Failed to delete client during teardown: {str(e)}")

    remove_test_db(TEST_DB_PATH)


def create_sample_documents(count: int = 1) -> List[Document]:
    """Helper function to create sample documents."""
    return [
        Document(
            page_content=f"Sample document content {i}",
            metadata={
                "doc_id": f"doc_{i}",
                "title": f"Document {i}",
                "source": "test"
            }
        ) for i in range(count)
    ]

def test_init_vector_store(vector_store_fixture: VectorStore):
    """Test if the vector store is initialized correctly."""
    assert os.path.exists(TEST_DB_PATH)
    assert vector_store_fixture.client is not None
    assert vector_store_fixture.collection is not None
    assert vector_store_fixture.collection.name == "news_articles"

def test_add_documents_success(vector_store_fixture: VectorStore):
    """Test adding documents to the vector store."""
    documents = create_sample_documents(3)
    try:
        vector_store_fixture.add_documents(documents)
        
        # Verify documents were added
        results = vector_store_fixture.collection.get()
        assert len(results["ids"]) == 3
        assert results["ids"][0] == "doc_0"
        assert results["documents"][0] == "Sample document content 0"
        assert results["metadatas"][0]["title"] == "Document 0"
    except Exception as e:
        pytest.fail(f"Failed to add documents: {str(e)}")

def test_add_documents_empty(vector_store_fixture: VectorStore):
    """Test adding empty list of documents."""
    with pytest.raises(Exception):
        vector_store_fixture.add_documents([])

def test_similarity_search_success(vector_store_fixture: VectorStore):
    """Test similarity search with documents in store."""
    documents = create_sample_documents(3)
    try:
        vector_store_fixture.add_documents(documents)
        
        results = vector_store_fixture.similarity_search("sample", k=2)
        assert len(results) == 2
        assert "sample" in results[0]["content"].lower()
        assert results[0]["metadata"]["title"] == "Document 0"
    except Exception as e:
        pytest.fail(f"Failed similarity search test: {str(e)}")

def test_similarity_search_empty(vector_store_fixture: VectorStore):
    """Test similarity search with empty store."""
    results = vector_store_fixture.similarity_search("query")
    assert len(results) == 0

def test_get_document_found(vector_store_fixture: VectorStore):
    """Test retrieving an existing document."""
    documents = create_sample_documents(1)
    try:
        vector_store_fixture.add_documents(documents)
        
        doc = vector_store_fixture.get_document("doc_0")
        assert doc is not None
        assert doc["id"] == "doc_0"
        assert doc["content"] == "Sample document content 0"
        assert doc["metadata"]["title"] == "Document 0"
    except Exception as e:
        pytest.fail(f"Failed get document test: {str(e)}")

def test_get_document_not_found(vector_store_fixture: VectorStore):
    """Test retrieving a non-existent document."""
    doc = vector_store_fixture.get_document("nonexistent")
    assert doc is None