import json
import langchain
from datetime import datetime
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
from loguru import logger
from langchain_core.output_parsers import JsonOutputParser

from backend.news_api import NewsAPI
from backend.data_store import DataStore
from backend.vector_store import VectorStore


langchain.debug = True


# Initialize text splitter with appropriate chunking parameters
class NewsRAG:
    def __init__(self, llm: BaseChatOpenAI, db: DataStore, vec_db: VectorStore, news_api: NewsAPI):
        """
        Initializes the NewsRAG pipeline.

        Args:
            llm: The language model instance.
            db: The data store instance for saving news and analysis.
            vec_db: The vector store instance for similarity search.
            news_api: The news API instance for fetching articles.
        """
        self.llm = llm
        self.db = db
        self.vec_db = vec_db
        self.news_api = news_api
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        
        # Define the prompt template for analysis
        self.analysis_prompt = ChatPromptTemplate.from_template("""
            你是一个专业的新闻分析师。请将以下英文新闻翻译为中文，并提供详细的影响分析。
            分析时请考虑以下几个方面：
            1. 新闻的重要性和影响范围
            2. 对相关国家和地区的潜在影响
            3. 可能带来的经济、政治或社会影响
            4. 未来可能的发展趋势
            5. id无需处理，直接输出即可

            
            请以JSON格式输出，包含以下字段：
            - id: 新闻ID标识
            - title: 中文标题
            - content: 中文内容
            - analysis: 影响分析
            - keywords: ["关键词1", "关键词2", "关键词3"],
            
            NewsID: {id}
            Content: {content}
            Source: {source}
            Context: {context}
        """)
        
        
        # Define output parser
        self.output_parser = JsonOutputParser()

    def retrieve_context(self, news: Dict) -> Dict:
        """
        Retrieves relevant historical news context from the vector store.

        Args:
            news: A dictionary representing the news article, must contain 'content'.

        Returns:
            The news dictionary updated with the 'context' key containing
            JSON string of similar historical news.

        Raises:
            Exception: If the similarity search fails.
        """
        try:
            results = self.vec_db.similarity_search(news["content"], k=3)
            context = json.dumps(results)
            logger.info(f"Retrieved {len(results)} relevant documents")
            news['context'] = context

        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            raise

        return news

    def save_news_db(self, news: Dict):
        """
        Saves the raw news article to the database and adds the generated ID to the news dictionary.

        Args:
            news: A dictionary representing the news article.

        Returns:
            The news dictionary updated with the 'id' key.
        """
        id = self.db.save_news(news)
        news["id"] = id

        return news

    def save_analysis_db(self, news: Dict):
        """
        Saves the analysis results (analysis text and keywords) to the database,
        associating it with the news ID.

        Args:
            news: A dictionary containing the news 'id', 'analysis', and 'keywords'.

        Returns:
            The original news dictionary.
        """
        self.db.save_analysis(news["id"], news["analysis"], news["keywords"])
        return news

    def mock_llm(self, news: Dict):
        """
        A mock function to simulate LLM analysis for testing purposes.

        Args:
            news: A dictionary representing the news article.

        Returns:
            The news dictionary updated with mock 'analysis' and 'keywords'.
        """
        news['analysis'] = "ayalysis results"
        news["keywords"] = ["key1", "key2"]

        return news
    
    def save_news_analysis_vec(self, news: Dict):
        """
        Stores the combined news content and analysis into the vector store after splitting.
        Removes 'context', 'content', and 'analysis' from the news dictionary before storing
        the rest as metadata.

        Args:
            news: A dictionary containing the news article data, including 'id', 'analysis',
                  'keywords', 'content', and potentially 'context'.
        """
        news.pop("context", None) # Use pop with default None to avoid KeyError if context wasn't added
        content = news.pop("content", "") + json.dumps(news.pop("analysis", ""))
        metadata = news
        metadata["keywords"] = json.dumps(metadata["keywords"])

        # from IPython.core.debugger import set_trace
        # set_trace()

        try:
            # Split content directly without temp files
            documents = [Document(page_content=content, metadata=metadata)]
            chunks = self.text_splitter.split_documents(documents)
            self.vec_db.add_documents(chunks)
            logger.info("Stored content in vectorstore")
        except Exception as e:
            logger.error(f"Failed to store to vectorstore: {e}")

    def start(self):
        """
        The main entry point to start the news analysis pipeline.
        Fetches top headlines, processes each article through the RAG chain
        (save raw news, retrieve context, analyze, save analysis, save to vector store).
        """
        articles = self.news_api.get_top_headlines()

        for article in articles:
            composed_news_chain = (
                RunnableLambda(self.save_news_db)
                | RunnableLambda(self.retrieve_context)
                | self.analysis_prompt
                | self.llm
                | self.output_parser
                | RunnableLambda(self.save_analysis_db)
                | RunnableLambda(self.save_news_analysis_vec)
            )

            composed_news_chain.invoke(article)
                