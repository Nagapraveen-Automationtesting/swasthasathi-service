import logging
import os
from pydantic.v1 import BaseSettings

# Import the new logging configuration
from src.config.logging_config import init_logging, get_logger

# Initialize comprehensive logging system
init_logging()

# Get the properly configured logger for this module
logger = get_logger(__name__)

class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    MONGO_CONNECTION_STRING:str
    debug:bool = False
    DATABASE:str
    BLOB_KEY:str
    BLOB_ACCOUNT_NAME:str
    BLOB_CONTAINER:str
    OCR_BASE_URL:str
    
    # JWT Configuration - THESE MUST BE SET IN ENVIRONMENT VARIABLES
    JWT_SECRET_KEY: str  # Must be set in .env file - no default for security
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour default
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days default
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = ""  # Comma-separated list of allowed origins
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_TO_CONSOLE: bool = True
    LOG_JSON_FORMAT: bool = False  # Set to True for production
    LOG_FILE_PATH: str = "logs/swasthasathi-service.log"

settings = Settings()

# Log the configuration loading
logger.info("Swasthasathi Service configuration loaded successfully", extra={
    'config': {
        'debug': settings.debug,
        'host': settings.HOST,
        'port': settings.PORT,
        'log_level': settings.LOG_LEVEL,
        'database': settings.DATABASE[:20] + "..." if len(settings.DATABASE) > 20 else settings.DATABASE
    }
})