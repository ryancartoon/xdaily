from langchain_deepseek import ChatDeepSeek
from config.settings import settings


LLM = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=settings.DEEPSEEK_API_KEY
)
