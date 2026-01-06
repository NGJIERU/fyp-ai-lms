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

    # AI / LLM settings
    # OpenAI (legacy - can be removed)
    OPENAI_API_KEY: Optional[str] = None
    USE_OPENAI_TUTOR: bool = False
    USE_OPENAI_EMBEDDINGS: bool = False
    
    # HuggingFace (primary - recommended)
    HUGGINGFACE_API_TOKEN: Optional[str] = None
    HUGGINGFACE_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"
    USE_HUGGINGFACE_TUTOR: bool = True

    # Google Gemini (disabled by default - quota issues on free tier)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    USE_GEMINI_TUTOR: bool = False
    
    # General AI settings
    AI_TUTOR_MODEL: str = "gpt-3.5-turbo"  # Fallback/legacy
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
