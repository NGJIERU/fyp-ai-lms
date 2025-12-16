from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered LMS"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "jieru_0901"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "lms_db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Security
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # AI / OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    AI_TUTOR_MODEL: str = "gpt-3.5-turbo"
    USE_OPENAI_TUTOR: bool = False
    USE_OPENAI_EMBEDDINGS: bool = False
    EMBEDDING_MODEL_NAME: str = "local_fast"
    BACKEND_CORS_ORIGINS: List[str] = []

    class Config:
        case_sensitive = True
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
