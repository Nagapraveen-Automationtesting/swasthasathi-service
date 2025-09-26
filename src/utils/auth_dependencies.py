from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from src.config.logging_config import get_logger, log_security_event
from src.utils.auth_utils import auth_utils
from src.models.User_Model import UserInDB, TokenData
from src.db.mongo_db import mongo

# Get logger for this module
logger = get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Dependency to get current user from JWT token
    Raises HTTPException if token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token
        token_data = auth_utils.verify_token(token, "access")
        if token_data is None:
            raise credentials_exception
            
        return token_data
    except Exception:
        raise credentials_exception

async def get_current_user(token_data: TokenData = Depends(get_current_user_token)) -> UserInDB:
    """
    Dependency to get current user object from database
    Raises HTTPException if user not found or inactive
    """
    try:
        # Get user from database
        user_data = await mongo.fetch_one("Users", {"email_id": token_data.email})
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Convert to UserInDB model
        user = UserInDB(**user_data)
        
        # Check if user is active
        if not user.status:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
            
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Dependency to get current active user
    This is an alias for get_current_user with explicit active check
    """
    return current_user

# Optional authentication dependency (doesn't raise exception if no token)
async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[UserInDB]:
    """
    Optional authentication dependency
    Returns None if no token provided or token is invalid
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        token_data = auth_utils.verify_token(token, "access")
        if token_data is None:
            return None
        
        user_data = await mongo.fetch_one("Users", {"email_id": token_data.email})
        if user_data is None:
            return None
        
        user = UserInDB(**user_data)
        if not user.status:
            return None
            
        return user
    except Exception:
        return None

# City-based authorization (replacing role-based for now)
def require_city(required_city: str):
    """
    Dependency factory for city-based authorization
    Usage: @app.get("/city-specific", dependencies=[Depends(require_city("New York"))])
    """
    async def city_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.city != required_city:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"City {required_city} access required"
            )
        return current_user
    return city_checker

def require_any_city(required_cities: list):
    """
    Dependency factory for multiple city authorization
    Usage: @app.get("/multi-city", dependencies=[Depends(require_any_city(["New York", "Boston"]))])
    """
    async def city_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.city not in required_cities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these cities required: {', '.join(required_cities)}"
            )
        return current_user
    return city_checker

# User ID based authorization
def require_user_id(required_user_id: int):
    """
    Dependency factory for user ID-based authorization
    """
    async def user_id_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.user_id != required_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        return current_user
    return user_id_checker
