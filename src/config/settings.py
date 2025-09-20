import logging
import os

from pydantic.v1 import BaseSettings

logger = logging.getLogger("People Cost")

class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    MONGO_CONNECTION_STRING:str
    debug:bool = False
    DATABASE:str
    BLOB_KEY:str
    BLOB_ACCOUNT_NAME:str
    BLOB_CONTAINER:str
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour default
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days default

settings= Settings()