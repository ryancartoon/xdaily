from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document
from loguru import logger

class VectorStore:
    def __init__(self, persist_directory: str = "chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        self.collection = self.client.get_or_create_collection(
            name="news_articles",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        try:
            ids = []
            texts = []
            metadatas = []
            
            for doc in documents:
                ids.append(doc.metadata.get("doc_id", str(len(ids))))
                texts.append(doc.page_content)
                metadatas.append(doc.metadata)
            
            self.collection.add(
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {str(e)}")
            raise

    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            return [{
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            } for i in range(len(results["ids"][0]))]
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {str(e)}")
            raise

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a specific document by ID"""
        try:
            results = self.collection.get(
                ids=[doc_id]
            )
            if results["ids"]:
                return {
                    "id": results["ids"][0],
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            raise 