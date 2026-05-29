from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_URL: str = "https://api.qnaigc.com/v1"
    API_KEY: str = "sk-07c8ec0cd1621fceb1038134cdba52bfcc069cdc49235e609827d1247d053728"
    MODEL_NAME: str = "deepseek-v3"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    WTTR_API_URL: str = "https://wttr.in"
    
    BOCHA_API_URL: str = "https://api.bocha.cn/v1/web-search"
    BOCHA_API_KEY: str = "sk-05ee5e6c56614bb2a3f8eb263150f975"
    
    class Config:
        env_file = ".env"


settings = Settings()