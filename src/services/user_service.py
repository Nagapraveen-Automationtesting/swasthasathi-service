import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from src.db.mongo_db import mongo
from src.models.User_Model import CREATE_USER, UPDATE_USER, UserInDB, USER_RESPONSE
from src.utils.auth_utils import auth_utils
from src.utils.util import convert_date_to_datetime


async def create_user(request: CREATE_USER) -> Dict[str, Any]:
    """Create a new user with all required fields"""
    try:
        # Hash the password
        hashed_password = auth_utils.get_password_hash(request.password)
        print(f"\n\n\nGoing into create_user :\n {request.password}\n\n\n\n")
        
        # Get the next user_id (auto-increment simulation)
        last_user = await mongo.fetch_one(
            "Users",
            {},
            sort=[("user_id", -1)]
        )
        next_user_id = (last_user["user_id"] + 1) if last_user else 1

        # Prepare user data with all fields
        user_data = {
            "user_id": next_user_id,
            "user_name": request.user_name,
            "gender": request.gender,
            "dob": convert_date_to_datetime(request.dob),
            "mobile_num": request.mobile_num,
            "email_id": request.email_id,
            "address": request.address,
            "city": request.city,
            "status": True,
            "created_on": datetime.utcnow(),
            "blood_group": request.blood_group,
            "height": request.height,
            "weight": request.weight,
            "diabetics": request.diabetics,
            "bp": request.bp,
            "hashed_password": hashed_password,
            # Extended fields for form data
            "emergency_contact_name": getattr(request, 'emergency_contact_name', None),
            "emergency_contact_phone": getattr(request, 'emergency_contact_phone', None),
            "emergency_contact_relation": getattr(request, 'emergency_contact_relation', None),
            "medical_conditions": getattr(request, 'medical_conditions', None),
            "allow_notifications": getattr(request, 'allow_notifications', True),
            "agree_to_terms": getattr(request, 'agree_to_terms', True),
            "agree_to_privacy": getattr(request, 'agree_to_privacy', True)
        }

        # Insert user into database
        result = await mongo.insert_one("Users", user_data)
        
        if result:
            return {
                "success": True,
                "user_id": next_user_id,
                "message": "User created successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to create user"
            }
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return {
            "success": False,
            "message": f"Error creating user: {str(e)}"
        }


async def update_user(request: UPDATE_USER) -> Dict[str, Any]:
    """Update user details"""
    try:
        # Prepare update data (only non-None fields)
        update_data = {k: v for k, v in request.dict().items() if v is not None and k != "user_id"}
        
        if not update_data:
            return {
                "success": False,
                "message": "No data to update"
            }
        
        # Update user in database
        result = await mongo.update_one(
            "Users",
            {"user_id": request.user_id},
            {"$set": update_data}
        )
        
        if result:
            return {
                "success": True,
                "message": "User updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "User not found or update failed"
            }
            
    except Exception as e:
        print(f"Error updating user: {e}")
        return {
            "success": False,
            "message": f"Error updating user: {str(e)}"
        }


async def get_user_by_id(user_id: int) -> Optional[UserInDB]:
    """Get user by user_id"""
    try:
        user_data = await mongo.fetch_one("Users", {"user_id": user_id})
        if user_data:
            # Remove MongoDB internal ID
            user_data.pop("_id", None)
            return UserInDB(**user_data)
        return None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None


async def get_user_by_email(email_id: str) -> Optional[UserInDB]:
    """Get user by email_id"""
    try:
        user_data = await mongo.fetch_one("Users", {"email_id": email_id})
        if user_data:
            # Remove MongoDB internal ID
            user_data.pop("_id", None)
            return UserInDB(**user_data)
        return None
    except Exception as e:
        print(f"Error fetching user by email: {e}")
        return None


async def get_all_users(skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Get all users with pagination"""
    try:
        # Count total users
        total_count = await mongo.count_documents("Users", {})
        
        # Fetch users with pagination
        users_data = await mongo.fetch_many(
            "Users", 
            {}, 
            skip=skip, 
            limit=limit,
            sort=[("created_on", -1)]
        )
        
        # Convert to response format (remove sensitive data)
        users = []
        for user_data in users_data:
            user_data.pop("_id", None)
            user_data.pop("hashed_password", None)
            users.append(USER_RESPONSE(**user_data))
        
        return {
            "success": True,
            "users": [user.dict() for user in users],
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        print(f"Error fetching users: {e}")
        return {
            "success": False,
            "message": f"Error fetching users: {str(e)}",
            "users": [],
            "total_count": 0
        }


async def delete_user(user_id: int) -> Dict[str, Any]:
    """Soft delete user by setting status to False"""
    try:
        result = await mongo.update_one(
            "Users",
            {"user_id": user_id},
            {"$set": {"status": False}}
        )
        
        if result:
            return {
                "success": True,
                "message": "User deactivated successfully"
            }
        else:
            return {
                "success": False,
                "message": "User not found"
            }
            
    except Exception as e:
        print(f"Error deactivating user: {e}")
        return {
            "success": False,
            "message": f"Error deactivating user: {str(e)}"
        }


async def search_users(query: str, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
    """Search users by name, email, or mobile number"""
    try:
        # Create search filter
        search_filter = {
            "$or": [
                {"user_name": {"$regex": query, "$options": "i"}},
                {"email_id": {"$regex": query, "$options": "i"}},
                {"mobile_num": {"$regex": query, "$options": "i"}},
                {"city": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Count total matching users
        total_count = await mongo.count_documents("Users", search_filter)
        
        # Fetch matching users
        users_data = await mongo.fetch_many(
            "Users", 
            search_filter, 
            skip=skip, 
            limit=limit,
            sort=[("created_on", -1)]
        )
        
        # Convert to response format
        users = []
        for user_data in users_data:
            user_data.pop("_id", None)
            user_data.pop("hashed_password", None)
            users.append(USER_RESPONSE(**user_data))
        
        return {
            "success": True,
            "users": [user.dict() for user in users],
            "total_count": total_count,
            "query": query,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        print(f"Error searching users: {e}")
        return {
            "success": False,
            "message": f"Error searching users: {str(e)}",
            "users": [],
            "total_count": 0
        }