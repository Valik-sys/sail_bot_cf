from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    TG_TOKEN: str = Field(..., env="TG_TOKEN")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    ADMIN_ID: int = Field(..., env="ADMIN_ID")
    MANAGER_CHAT_ID: int = Field(..., env="MANAGER_CHAT_ID")  # ID чата/группы менеджеров
    
    # Настройки бота
    RATING_TIME: int = 5  # минуты
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
