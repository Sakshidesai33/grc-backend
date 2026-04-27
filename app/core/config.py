import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grc.db")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "GRCSYSTEMSECRET2024")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # API
    API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
    PROJECT_NAME = os.getenv("PROJECT_NAME", "GRC AI System")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
