from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime, date

class LOGIN_MODEL(BaseModel):
    email: str
    password: str

class GETUSER(BaseModel):
    user_id: int

class CREATE_USER(BaseModel):
    user_name: str
    gender: str
    dob: date
    mobile_num: str
    email_id: str
    address: Optional[str] = "Not provided"
    city: Optional[str] = "Not provided"
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    diabetics: bool = False
    bp: Optional[str] = None
    password: str
    # New fields for extended form data
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    medical_conditions: Optional[List[str]] = None
    allow_notifications: bool = True
    agree_to_terms: bool = True
    agree_to_privacy: bool = True

class FORM_SIGNUP_DATA(BaseModel):
    """Model for handling form data from frontend"""
    user_name: str
    gender: str
    dob: date
    mobile_num: str
    email_id: str
    address: Optional[str] = "Not provided"
    city: Optional[str] = "Not provided"
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    diabetics: bool = False
    bp: Optional[str] = None
    password: str
    # New fields for extended form data
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    medical_conditions: Optional[List[str]] = None
    allow_notifications: bool = True
    agree_to_terms: bool = True
    agree_to_privacy: bool = True

class UPDATE_USER(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    mobile_num: Optional[str] = None
    email_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    diabetics: Optional[bool] = None
    bp: Optional[str] = None

class USER_RESPONSE(BaseModel):
    user_id: int
    user_name: str
    gender: str
    dob: date
    mobile_num: str
    email_id: str
    address: str
    city: str
    status: bool
    created_on: datetime
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    diabetics: bool = False
    bp: Optional[str] = None

# JWT Token Models
class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    mobile_num: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# MongoDB Token Storage Model
class TokenStore(BaseModel):
    user_id: str  # user_id as string
    refresh_token: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    device_info: Optional[str] = None

# User Authentication Model
class UserInDB(BaseModel):
    user_id: int
    user_name: str
    gender: str
    dob: Union[date, datetime]
    mobile_num: str
    email_id: str
    address: str
    city: str
    status: bool = True
    created_on: datetime
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    diabetics: bool = False
    bp: Optional[str] = None
    hashed_password: Optional[str] = None
    # Extended fields
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    medical_conditions: Optional[List[str]] = None
    allow_notifications: bool = True
    agree_to_terms: bool = True
    agree_to_privacy: bool = True

# Change Password Model
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Upload Status Model
class UploadStatusRequest(BaseModel):
    userId: int
    filename: str
    file_url: str
    status: str
    upload_timestamp: datetime

class UploadStatusResponse(BaseModel):
    success: bool
    message: str
    upload_id: Optional[str] = None