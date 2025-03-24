from typing import List, Dict

from langchain.prompts.chat import ChatPromptTemplate
from langchain.chains import LLMChain
from loguru import logger

from config.settings import settings
from backend.core.exceptions import AnalysisError
from langchain_deepseek import ChatDeepSeek
from backend.core.document import NewsDocument



class ChatBox:
    """
    前端可以通过聊天窗口随时做实事分析
    """
    def __init__(self, llm):
        self.llm = llm

        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的新闻分析助手。你可以：
            1. 回答用户关于新闻的问题
            2. 分析新闻之间的关联
            3. 解释新闻背景
            4. 提供专业的见解
            
            请基于以下新闻上下文回答用户的问题：
            
            {context}
            """),
            ("user", "{question}")
        ])
    
    


class NewsAnalysis:
    def __init__(self):
        self.llm = ChatDeepSeek(api_key=settings.DEEPSEEK_API_KEY)
        
        # Define analysis prompts
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的新闻分析师。请将以下英文新闻翻译为中文，并提供详细的影响分析。
            分析时请考虑以下几个方面：
            1. 新闻的重要性和影响范围
            2. 对相关国家和地区的潜在影响
            3. 可能带来的经济、政治或社会影响
            4. 未来可能的发展趋势

            
            请以JSON格式输出，包含以下字段：
            - title: 中文标题
            - content: 中文内容
            - analysis: 影响分析
            - keywords: ["关键词1", "关键词2", "关键词3"],
            """),
            ("user", "{text}")
        ])
        
    def analyze_documents(self, documents: List[NewsDocument]) -> List[NewsDocument]:
        """Analyze a list of documents"""
        try:
            analyzed_docs = []
            for doc in documents:
                chain = self.analysis_prompt | self.model | self.output_parser
                
                # 执行分析
                result = chain.invoke({"text": doc.page_content})

            return analyzed_docs
        except Exception as e:
            logger.error(f"Failed to analyze documents: {str(e)}")
            raise AnalysisError("Failed to analyze documents") from e

    def analyze_single_document(self, document: NewsDocument) -> NewsDocument:
        """Analyze a single document"""
        try:
            # Generate summary
            summary_chain = LLMChain(llm=self.llm, prompt=self.summary_prompt)
            summary = summary_chain.run(document.content)
            
            # Generate analysis
            analysis_chain = LLMChain(llm=self.llm, prompt=self.analysis_prompt)
            analysis_result = analysis_chain.run(document.content)
            
            # Generate tags
            tags_chain = LLMChain(llm=self.llm, prompt=self.tags_prompt)
            tags = tags_chain.run(document.content)
            
            # Create new NewsDocument with analysis results
            return NewsDocument(
                title=document.title,
                source=document.source,
                published_at=document.published_at,
                content=document.content,
                description=document.description,
                url=document.url,
                author=document.author,
                urlToImage=document.urlToImage,
                summary=summary,
                analysis_result=analysis_result,
                tags=tags
            )
        except Exception as e:
            logger.error(f"Failed to analyze document: {str(e)}")
            raise AnalysisError("Failed to analyze document") from e 