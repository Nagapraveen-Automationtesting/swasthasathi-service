import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from src.config.settings import settings
from src.models.User_Model import TokenData, UserInDB
from src.db.mongo_db import mongo

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthUtils:
    """Utility class for JWT authentication operations"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        print(f"<<<<<<<<<<<<<<<<{plain_password} **** {hashed_password}>>>>>>>>>>>>>>>>>>")
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Add unique identifier for refresh token
        to_encode.update({
            "exp": expire, 
            "type": "refresh",
            "jti": str(uuid.uuid4())  # JWT ID for token blacklisting
        })
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify JWT token and return token data"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
                
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            mobile_num: str = payload.get("mobile_num")
            
            if email is None:
                return None
                
            token_data = TokenData(email=email, user_id=user_id, mobile_num=mobile_num)
            return token_data
            
        except JWTError:
            return None
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password"""
        try:
            # Get user from database
            user_data = await mongo.fetch_one("Users", {"email_id": email})
            print(f"Mongo result : {user_data}")
            if not user_data:
                return None
            
            # Check if user has hashed password (for new authentication system)
            if "hashed_password" not in user_data or not user_data["hashed_password"]:
                # For existing users without hashed passwords, you might want to 
                # implement a migration strategy here
                return None
            
            # Verify password
            if not AuthUtils.verify_password(password, user_data["hashed_password"]):
                return None
            user_data.pop("_id")
            # Convert to UserInDB model
            print()
            print(type(user_data['dob']))
            print()
            user = UserInDB(**user_data)
            return user
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    @staticmethod
    async def create_user_tokens(user: UserInDB) -> Dict[str, Any]:
        """Create both access and refresh tokens for a user"""
        # Token payload with required user information
        token_payload = {
            "sub": user.email_id,  # Primary identifier
            "user_id": user.user_id,
            "mobile_num": user.mobile_num,
            "email_id": user.email_id,
            "user_name": user.user_name,
            "city": user.city,
            "status": user.status
        }
        
        # Create tokens
        access_token = AuthUtils.create_access_token(token_payload)
        refresh_token = AuthUtils.create_refresh_token({
            "sub": user.email_id, 
            "user_id": user.user_id,
            "mobile_num": user.mobile_num
        })
        
        # Store refresh token in database
        await AuthUtils.store_refresh_token(
            user_id=str(user.user_id),
            refresh_token=refresh_token
        )
        
        # User info for response
        user_info = {
            "user_id": user.user_id,
            "user_name": user.user_name,
            "email_id": user.email_id,
            "mobile_num": user.mobile_num,
            "city": user.city,
            "status": user.status
        }
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
            "user_info": user_info
        }
    
    @staticmethod
    async def store_refresh_token(user_id: str, refresh_token: str, device_info: str = None) -> bool:
        """Store refresh token in MongoDB"""
        try:
            # Decode token to get expiry
            payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            expires_at = datetime.fromtimestamp(payload["exp"])
            
            token_doc = {
                "user_id": user_id,
                "refresh_token": refresh_token,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_active": True,
                "device_info": device_info,
                "jti": payload.get("jti")
            }
            
            # Insert token document
            result = await mongo.insert_one("TokenStore", token_doc)
            return result is not None
            
        except Exception as e:
            print(f"Error storing refresh token: {e}")
            return False
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """Generate new access token using refresh token"""
        try:
            # Verify refresh token
            token_data = AuthUtils.verify_token(refresh_token, "refresh")
            if not token_data:
                return None
            
            # Check if refresh token exists and is active in database
            token_doc = await mongo.fetch_one("TokenStore", {
                "refresh_token": refresh_token,
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not token_doc:
                return None
            
            # Get user data
            user_data = await mongo.fetch_one("Users", {"email_id": token_data.email})
            if not user_data:
                return None
            
            # Create new access token
            token_payload = {
                "sub": user_data["email_id"],
                "user_id": user_data["user_id"],
                "mobile_num": user_data["mobile_num"],
                "email_id": user_data["email_id"],
                "user_name": user_data["user_name"],
                "city": user_data["city"],
                "status": user_data["status"]
            }
            
            access_token = AuthUtils.create_access_token(token_payload)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return None
    
    @staticmethod
    async def revoke_refresh_token(refresh_token: str) -> bool:
        """Revoke a refresh token"""
        try:
            result = await mongo.update_one(
                "TokenStore",
                {"refresh_token": refresh_token},
                {"$set": {"is_active": False, "revoked_at": datetime.utcnow()}}
            )
            return result is not None
        except Exception as e:
            print(f"Error revoking token: {e}")
            return False
    
    @staticmethod
    async def revoke_all_user_tokens(user_id: str) -> bool:
        """Revoke all refresh tokens for a user"""
        try:
            result = await mongo.update_many(
                "TokenStore",
                {"user_id": user_id, "is_active": True},
                {"$set": {"is_active": False, "revoked_at": datetime.utcnow()}}
            )
            return result is not None
        except Exception as e:
            print(f"Error revoking user tokens: {e}")
            return False
    
    @staticmethod
    async def cleanup_expired_tokens():
        """Remove expired tokens from database"""
        try:
            result = await mongo.delete_many(
                "TokenStore",
                {"expires_at": {"$lt": datetime.utcnow()}}
            )
            return result
        except Exception as e:
            print(f"Error cleaning up tokens: {e}")
            return None

# Create instance for easy access
auth_utils = AuthUtils()
