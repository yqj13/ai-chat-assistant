from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_URL: str = "https://api.qnaigc.com/v1"
    API_KEY: str = "sk-07c8ec0cd1621fceb1038134cdba52bfcc069cdc49235e609827d1247d053728"
    MODEL_NAME: str = "deepseek-v3"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    WTTR_API_URL: str = "https://wttr.in"
    SO_SEARCH_URL: str = "https://www.so.com"
    
    class Config:
        env_file = ".env"


settings = Settings()