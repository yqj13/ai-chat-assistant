from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_URL: str = "https://api.qnaigc.com/v1"
    API_KEY: str = "sk-07c8ec0cd1621fceb1038134cdba52bfcc069cdc49235e609827d1247d053728"
    MODEL_NAME: str = "deepseek/deepseek-v3.2-exp-thinking"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    WTTR_API_URL: str = "https://wttr.in"
    
    BOCHA_API_URL: str = "https://api.bocha.cn/v1/web-search"
    BOCHA_API_KEY: str = "sk-05ee5e6c56614bb2a3f8eb263150f975"
    
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "111111"
    DB_NAME: str = "ai_chat"
    
    class Config:
        env_file = ".env"


settings = Settings()