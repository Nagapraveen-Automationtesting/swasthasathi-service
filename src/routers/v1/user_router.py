from typing import Dict, List, Any
import logging
import json
from datetime import datetime, date
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query, Request

from src.config.settings import logger
from src.db.mongo_db import mongo
from src.models.User_Model import (
    GETUSER, CREATE_USER, UPDATE_USER, LOGIN_MODEL, Token, 
    RefreshTokenRequest, UserInDB, USER_RESPONSE, ChangePasswordRequest,
    FORM_SIGNUP_DATA
)
from src.services.user_service import (
    create_user, update_user, get_user_by_id, get_all_users, 
    delete_user, search_users
)
from src.utils.auth_utils import auth_utils
from src.utils.auth_dependencies import get_current_user, get_current_user_token

user_router = APIRouter()


@user_router.post("/login", response_model=Token)
async def login(credentials: LOGIN_MODEL = Body(...)):
    """
    Authenticate user and return JWT tokens
    """
    try:
        # Authenticate user
        print(f"\n\n\n{credentials.email}, {credentials.password}\n\n")
        user = await auth_utils.authenticate_user(credentials.email, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        token_data = await auth_utils.create_user_tokens(user)
        
        logger.info(f"User {user.email_id} logged in successfully")
        return Token(**token_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@user_router.post("/register", response_model=Dict[str, Any])
async def register(user_data: CREATE_USER = Body(...)):
    """
    Register a new user
    """
    try:
        # Check if user already exists
        existing_user = await mongo.fetch_one("Users", {"email_id": user_data.email_id})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check if mobile number already exists
        existing_mobile = await mongo.fetch_one("Users", {"mobile_num": user_data.mobile_num})
        if existing_mobile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this mobile number already exists"
            )
        
        # Create user
        result = await create_user(user_data)
        
        if result["success"]:
            logger.info(f"New user registered: {user_data.email_id}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


# @user_router.post("/signup-debug")
# async def signup_debug(request: Request):
#     """
#     Debug endpoint to see raw request data and validation errors
#     """
#     try:
#         # Get raw request body
#         body = await request.body()
#         logger.info(f"📥 Raw request body: {body.decode('utf-8')}")
        
#         # Try to parse as JSON
#         try:
#             json_data = json.loads(body.decode('utf-8'))
#             logger.info(f"📊 Parsed JSON data: {json.dumps(json_data, indent=2)}")
            
#             # Try to validate with FORM_SIGNUP_DATA
#             try:
#                 form_data = FORM_SIGNUP_DATA(**json_data)
#                 logger.info(f"✅ Successfully validated as FORM_SIGNUP_DATA")
#                 return {
#                     "status": "valid_form_data",
#                     "message": "Data can be processed by /signup-form endpoint",
#                     "parsed_data": json_data,
#                     "recommendation": "Use POST /user/signup-form with this data"
#                 }
#             except Exception as form_error:
#                 logger.error(f"❌ FORM_SIGNUP_DATA validation error: {form_error}")
                
#             # Try to validate with CREATE_USER
#             try:
#                 create_user_data = CREATE_USER(**json_data)
#                 logger.info(f"✅ Successfully validated as CREATE_USER")
#                 return {
#                     "status": "valid_create_user_data",
#                     "message": "Data can be processed by /signup endpoint",
#                     "parsed_data": json_data,
#                     "recommendation": "Use POST /user/signup with this data"
#                 }
#             except Exception as create_error:
#                 logger.error(f"❌ CREATE_USER validation error: {create_error}")
                
#             return {
#                 "status": "validation_failed",
#                 "message": "Data doesn't match any expected format",
#                 "raw_data": json_data,
#                 "form_validation_error": str(form_error),
#                 "create_user_validation_error": str(create_error),
#                 "recommendations": [
#                     "Check field names match the expected model",
#                     "Ensure data types are correct",
#                     "Use /signup-form for form data structure",
#                     "Use /signup for internal data structure"
#                 ]
#             }
            
#         except json.JSONDecodeError as json_error:
#             logger.error(f"❌ JSON parsing error: {json_error}")
#             return {
#                 "status": "invalid_json",
#                 "message": "Request body is not valid JSON",
#                 "raw_body": body.decode('utf-8'),
#                 "error": str(json_error)
#             }
            
#     except Exception as e:
#         logger.error(f"❌ Debug endpoint error: {e}")
#         return {
#             "status": "debug_error",
#             "message": "Error in debug endpoint",
#             "error": str(e)
#         }


@user_router.post("/signup", response_model=Dict[str, Any])
async def signup(user_data: CREATE_USER = Body(...)):
    """
    User signup service with confirmation response
    Creates user in database and returns detailed confirmation
    """
    try:
        # Log parsed data for debugging
        logger.info(f"📋 /signup received user_data: {user_data}")
        
        # Validate required fields
        if not user_data.email_id or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Check if user already exists by email
        existing_user = await mongo.fetch_one("Users", {"email_id": user_data.email_id})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "User already exists",
                    "message": f"An account with email {user_data.email_id} already exists",
                    "suggestion": "Please use a different email or try logging in"
                }
            )
        
        # Check if mobile number already exists
        existing_mobile = await mongo.fetch_one("Users", {"mobile_num": user_data.mobile_num})
        if existing_mobile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Mobile number already registered",
                    "message": f"An account with mobile number {user_data.mobile_num} already exists",
                    "suggestion": "Please use a different mobile number"
                }
            )
        
        # Create user in database
        result = await create_user(user_data)
        
        if result["success"]:
            # Get the created user details for confirmation
            created_user = await mongo.fetch_one("Users", {"user_id": result["user_id"]})
            if created_user:
                # Remove sensitive data
                created_user.pop("_id", None)
                created_user.pop("hashed_password", None)
                
                # Prepare confirmation response
                confirmation_response = {
                    "success": True,
                    "message": "User account created successfully",
                    "status": "ACCOUNT_CREATED",
                    "user_details": {
                        "user_id": created_user["user_id"],
                        "user_name": created_user["user_name"],
                        "email_id": created_user["email_id"],
                        "mobile_num": created_user["mobile_num"],
                        "city": created_user["city"],
                        "gender": created_user["gender"],
                        "status": created_user["status"],
                        "created_on": created_user["created_on"].isoformat(),
                        "account_type": "STANDARD",
                        "profile_completion": "BASIC"
                    },
                    "next_steps": [
                        "Verify your email address",
                        "Complete your profile information",
                        "Login to access your dashboard"
                    ],
                    "additional_info": {
                        "health_profile_status": "CREATED" if any([
                            created_user.get("blood_group"),
                            created_user.get("height"),
                            created_user.get("weight"),
                            created_user.get("bp")
                        ]) else "INCOMPLETE",
                        "total_users_in_system": await mongo.count_documents("Users", {"status": True}),
                        "registration_timestamp": created_user["created_on"].isoformat(),
                        "account_activation": "ACTIVE"
                    }
                }
                
                logger.info(f"User signup successful: {user_data.email_id} (ID: {result['user_id']})")
                return confirmation_response
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User created but confirmation failed"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Signup failed",
                    "message": result.get("message", "Unknown error occurred"),
                    "suggestion": "Please try again or contact support"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred during signup",
                "suggestion": "Please try again later or contact support"
            }
        )


def convert_form_data_to_create_user(form_data: FORM_SIGNUP_DATA) -> CREATE_USER:
    """
    Convert form data to CREATE_USER format with proper type conversions
    """
    try:
        # Convert date string to date object
        try:
            print(type(form_data.dob))
            # dob = datetime.strptime(form_data.dob, "%Y-%m-%d").date()
            dob = form_data.dob
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Please use YYYY-MM-DD format."
            )
        
        # Convert string values to appropriate types
        height = None
        if form_data.height and form_data.height:
            try:
                height = float(form_data.height)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid height value. Please provide a numeric value."
                )
        
        weight = None
        if form_data.weight and form_data.weight:
            try:
                weight = float(form_data.weight)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid weight value. Please provide a numeric value."
                )
        
        # Convert string booleans to actual booleans
        allow_notifications = form_data.allow_notifications == True if form_data.allow_notifications else True
        agree_to_terms = form_data.agree_to_terms == True if form_data.agree_to_terms else True
        agree_to_privacy = form_data.agree_to_privacy == True if form_data.agree_to_privacy else True
        
        # Check if user has diabetes based on medical conditions
        diabetics = False
        if form_data.medical_conditions:
            medical_conditions_lower = form_data.medical_conditions
            diabetics = "diabetes" in medical_conditions_lower or "diabetic" in medical_conditions_lower
        
        # Create CREATE_USER object
        create_user_data = CREATE_USER(
            user_name=form_data.user_name,
            gender=form_data.gender,
            dob=dob,
            mobile_num=form_data.mobile_num,
            email_id=form_data.email_id,
            address="Not provided",  # Not in form data
            city="Not provided",     # Not in form data
            blood_group=form_data.blood_group,
            height=height,
            weight=weight,
            diabetics=diabetics,
            bp=None,  # Not in form data
            password=form_data.password,
            emergency_contact_name=form_data.emergency_contact_name,
            emergency_contact_phone=form_data.emergency_contact_phone,
            emergency_contact_relation=form_data.emergency_contact_relation,
            medical_conditions=form_data.medical_conditions,
            allow_notifications=allow_notifications,
            agree_to_terms=agree_to_terms,
            agree_to_privacy=agree_to_privacy
        )
        
        return create_user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting form data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid form data: {str(e)}"
        )


@user_router.post("/signup-form", response_model=Dict[str, Any])
async def signup_form(form_data: FORM_SIGNUP_DATA = Body(...)):
    """
    User signup service for form data with confirmation response
    Handles form data structure and converts to internal format
    """
    try:
        # Log parsed form data for debugging
        logger.info(f"📋 /signup-form received form_data: {form_data}")
        
        # Validate required terms agreement
        if not (form_data.agree_to_terms and form_data.agree_to_terms == True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Terms agreement required",
                    "message": "You must agree to the terms and conditions to create an account",
                    "field": "agree_to_terms"
                }
            )
        
        if not (form_data.agree_to_privacy and form_data.agree_to_privacy == True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Privacy policy agreement required",
                    "message": "You must agree to the privacy policy to create an account",
                    "field": "agree_to_privacy"
                }
            )
        
        # Convert form data to internal format
        user_data = convert_form_data_to_create_user(form_data)
        
        print(f"user_data : {user_data}")
        existing_user = await mongo.fetch_one("Users", {"email_id": user_data.email_id})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "User already exists",
                    "message": f"An account with email {user_data.email_id} already exists",
                    "suggestion": "Please use a different email or try logging in",
                    "field": "email"
                }
            )
        
        # Check if mobile number already exists
        existing_mobile = await mongo.fetch_one("Users", {"mobile_num": user_data.mobile_num})
        if existing_mobile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Mobile number already registered",
                    "message": f"An account with mobile number {user_data.mobile_num} already exists",
                    "suggestion": "Please use a different mobile number",
                    "field": "phone"
                }
            )
        
        # Create user in database
        print(f">>>. Going into create_user")
        result = await create_user(user_data)

        if result["success"]:
            # Get the created user details for confirmation
            created_user = await mongo.fetch_one("Users", {"user_id": result["user_id"]})
            if created_user:
                # Remove sensitive data
                created_user.pop("_id", None)
                created_user.pop("hashed_password", None)
                
                # Determine if emergency contact is provided
                has_emergency_contact = bool(
                    created_user.get("emergency_contact_name") and 
                    created_user.get("emergency_contact_phone")
                )
                
                # Prepare comprehensive confirmation response
                confirmation_response = {
                    "success": True,
                    "message": "Account created successfully with form data",
                    "status": "ACCOUNT_CREATED",
                    "user_details": {
                        "user_id": created_user["user_id"],
                        "user_name": created_user["user_name"],
                        "email_id": created_user["email_id"],
                        "mobile_num": created_user["mobile_num"],
                        "gender": created_user["gender"],
                        "date_of_birth": created_user["dob"].isoformat(),
                        "status": created_user["status"],
                        "created_on": created_user["created_on"].isoformat(),
                        "account_type": "STANDARD",
                        "profile_completion": "COMPREHENSIVE"
                    },
                    "health_profile": {
                        "blood_group": created_user.get("blood_group"),
                        "height": created_user.get("height"),
                        "weight": created_user.get("weight"),
                        "diabetics": created_user.get("diabetics", False),
                        "medical_conditions": created_user.get("medical_conditions"),
                        "profile_status": "COMPLETE" if any([
                            created_user.get("blood_group"),
                            created_user.get("height"),
                            created_user.get("weight"),
                            created_user.get("medical_conditions")
                        ]) else "BASIC"
                    },
                    "emergency_contact": {
                        "name": created_user.get("emergency_contact_name"),
                        "phone": created_user.get("emergency_contact_phone"),
                        "relation": created_user.get("emergency_contact_relation"),
                        "status": "PROVIDED" if has_emergency_contact else "NOT_PROVIDED"
                    },
                    "preferences": {
                        "allow_notifications": created_user.get("allow_notifications", True),
                        "terms_agreed": created_user.get("agree_to_terms", True),
                        "privacy_agreed": created_user.get("agree_to_privacy", True)
                    },
                    "next_steps": [
                        "Verify your email address",
                        "Login to access your dashboard",
                        "Complete any remaining profile information"
                    ],
                    "additional_info": {
                        "total_users_in_system": await mongo.count_documents("Users", {"status": True}),
                        "registration_timestamp": created_user["created_on"].isoformat(),
                        "account_activation": "ACTIVE",
                        "data_completeness": "HIGH"
                    }
                }
                
                logger.info(f"Form signup successful: {user_data.email_id} (ID: {result['user_id']})")
                return confirmation_response
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User created but confirmation failed"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Signup failed",
                    "message": result.get("message", "Unknown error occurred"),
                    "suggestion": "Please try again or contact support"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred during signup",
                "suggestion": "Please try again later or contact support"
            }
        )


@user_router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    try:
        token_data = await auth_utils.refresh_access_token(request.refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        return token_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@user_router.post("/logout")
async def logout(request: RefreshTokenRequest, current_user: UserInDB = Depends(get_current_user)):
    """
    Logout user by revoking refresh token
    """
    try:
        success = await auth_utils.revoke_refresh_token(request.refresh_token)
        if success:
            logger.info(f"User {current_user.email_id} logged out successfully")
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to logout"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@user_router.post("/logout-all")
async def logout_all_devices(current_user: UserInDB = Depends(get_current_user)):
    """
    Logout user from all devices by revoking all refresh tokens
    """
    try:
        success = await auth_utils.revoke_all_user_tokens(str(current_user.user_id))
        if success:
            logger.info(f"User {current_user.email_id} logged out from all devices")
            return {"message": "Logged out from all devices successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to logout from all devices"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@user_router.get("/profile", response_model=USER_RESPONSE)
async def get_user_profile(current_user: UserInDB = Depends(get_current_user)):
    """
    Get current user's profile information
    """
    try:
        # Convert to response format (without sensitive data)
        profile_data = USER_RESPONSE(
            user_id=current_user.user_id,
            user_name=current_user.user_name,
            gender=current_user.gender,
            dob=current_user.dob,
            mobile_num=current_user.mobile_num,
            email_id=current_user.email_id,
            address=current_user.address,
            city=current_user.city,
            status=current_user.status,
            created_on=current_user.created_on,
            blood_group=current_user.blood_group,
            height=current_user.height,
            weight=current_user.weight,
            diabetics=current_user.diabetics,
            bp=current_user.bp
        )
        
        logger.info(f"Profile data fetched for user {current_user.email_id}")
        return profile_data
        
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile"
        )


@user_router.get("/users", response_model=Dict[str, Any])
async def get_all_users_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all users with pagination (Protected endpoint)
    """
    try:
        result = await get_all_users(skip=skip, limit=limit)
        if result["success"]:
            logger.info(f"Users list fetched by {current_user.email_id}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@user_router.get("/users/search", response_model=Dict[str, Any])
async def search_users_endpoint(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Search users by name, email, mobile, or city
    """
    try:
        result = await search_users(query=q, skip=skip, limit=limit)
        if result["success"]:
            logger.info(f"User search performed by {current_user.email_id} with query: {q}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )


@user_router.get("/users/{user_id}", response_model=USER_RESPONSE)
async def get_user_by_id_endpoint(
    user_id: int,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get user details by User ID (Protected endpoint)
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert to response format
        user_response = USER_RESPONSE(
            user_id=user.user_id,
            user_name=user.user_name,
            gender=user.gender,
            dob=user.dob,
            mobile_num=user.mobile_num,
            email_id=user.email_id,
            address=user.address,
            city=user.city,
            status=user.status,
            created_on=user.created_on,
            blood_group=user.blood_group,
            height=user.height,
            weight=user.weight,
            diabetics=user.diabetics,
            bp=user.bp
        )
        
        logger.info(f"User details fetched for user_id {user_id} by {current_user.email_id}")
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user details"
        )


@user_router.put("/users/{user_id}", response_model=Dict[str, Any])
async def update_user_endpoint(
    user_id: int,
    user_data: UPDATE_USER,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update user details (Protected endpoint)
    """
    try:
        # Set the user_id from the path parameter
        user_data.user_id = user_id
        
        result = await update_user(user_data)
        
        if result["success"]:
            logger.info(f"User details updated for user_id {user_id} by {current_user.email_id}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user details"
        )


@user_router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user_endpoint(
    user_id: int,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Deactivate user (soft delete) (Protected endpoint)
    """
    try:
        result = await delete_user(user_id)
        
        if result["success"]:
            logger.info(f"User {user_id} deactivated by {current_user.email_id}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@user_router.post("/change-password", response_model=Dict[str, str])
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Change user password (Protected endpoint)
    """
    try:
        # Verify current password
        if not current_user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account not set up for password authentication"
            )
        
        if not auth_utils.verify_password(request.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = auth_utils.get_password_hash(request.new_password)
        
        # Update password in database
        result = await mongo.update_one(
            "Users",
            {"user_id": current_user.user_id},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        
        if result:
            # Revoke all existing tokens to force re-login
            await auth_utils.revoke_all_user_tokens(str(current_user.user_id))
            
            logger.info(f"Password changed for user {current_user.email_id}")
            return {"message": "Password changed successfully. Please login again."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )