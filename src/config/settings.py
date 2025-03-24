from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Literal


class Settings(BaseSettings):
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
    DEEPSEEK_API_KEY: str = Field(..., env="DEEPSEEK_API_KEY")
    NEWSAPI_KEY: str = Field(..., env="NEWSAPI_KEY")
    OUTPUT_DIR: Path = Path("reports")
    LANGCHAIN_DEBUG: str = Field(..., env="LANGCHAIN_DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()