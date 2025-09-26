from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict
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

# Alias for form data - same structure as CREATE_USER
FORM_SIGNUP_DATA = CREATE_USER

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
    document_id: Optional[int] = None

class UploadStatusResponse(BaseModel):
    success: bool
    message: str
    upload_id: Optional[str] = None

# Pagination Models
class PaginationQuery(BaseModel):
    page: Optional[int] = Field(default=1, ge=1, description="Page number (starts from 1)")
    limit: Optional[int] = Field(default=10, ge=1, le=100, description="Number of items per page")
    
class PaginationInfo(BaseModel):
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool

# Document Models
class DocumentResponse(BaseModel):
    userId: int
    document_id: int
    original_filename: Optional[str] = None  # Original filename before sanitization
    filename: str  # Sanitized filename used for storage
    file_url: str
    blob_path: Optional[str] = None  # Add blob_path field
    status: str
    upload_timestamp: datetime
    created_at: datetime
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    # Vitals extraction fields for frontend handling
    vital_extracted: Optional[bool] = None  # Whether vitals were successfully extracted
    vitals_count: Optional[int] = None  # Number of vitals found
    vitals_processing_status: Optional[str] = None  # pending, completed, failed
    vitals_updated_at: Optional[datetime] = None  # When vitals processing was completed
    vitals_error: Optional[str] = None  # Error message if vitals extraction failed

class GetDocumentsResponse(BaseModel):
    success: bool
    message: str
    documents: List[DocumentResponse]
    pagination: PaginationInfo

# Vitals Models
class VitalData(BaseModel):
    value: str
    unit: str
    timestamp: str
    reference_range: Optional[str] = None
    status: Optional[str] = None
    original_name: Optional[str] = None

class VitalsMetadata(BaseModel):
    filename: Optional[str] = None
    container_name: Optional[str] = None
    blob_path: Optional[str] = None
    text_character_count: Optional[int] = None
    total_vitals_found: Optional[int] = None
    extraction_method: Optional[str] = None
    extraction_status: Optional[str] = None
    token_usage: Optional[Dict] = None

class VitalsResponse(BaseModel):
    document_id: int
    user_id: str
    report_id: str
    uploaded_at: str
    vitals: Dict[str, VitalData]
    source: Optional[str] = None
    metadata: Optional[VitalsMetadata] = None

class GetVitalsResponse(BaseModel):
    success: bool
    message: str
    vitals_data: Dict = None

# Signed URL Models
class SignedUrlRequest(BaseModel):
    blob_path: str = Field(..., description="The blob file path to generate signed URL for")

class SignedUrlResponse(BaseModel):
    success: bool
    message: str
    signed_url: Optional[str] = None
    expires_in: Optional[int] = None  # seconds until expiration