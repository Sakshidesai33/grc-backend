import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grc.db")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "GRCSYSTEMSECRET2024")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # API
    API_V1_STR = "/api/v1"
    PROJECT_NAME = "GRC AI System"

settings = Settings()
