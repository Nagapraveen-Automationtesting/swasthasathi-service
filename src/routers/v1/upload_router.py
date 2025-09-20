from datetime import datetime, timedelta

from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from fastapi import APIRouter, Form, Depends, HTTPException

from src.config.settings import settings, logger
from src.models.User_Model import UserInDB, UploadStatusRequest, UploadStatusResponse
from src.utils.auth_dependencies import get_current_user
from src.db.mongo_db import mongo

upload_router = APIRouter()


@upload_router.post("/generate-upload-url")
async def generate_upload_url(
    filename: str = Form(...), 
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a SAS token for blob upload (Protected endpoint)
    """
    try:
        sas_token = generate_blob_sas(
            account_name=settings.BLOB_ACCOUNT_NAME,
            container_name=settings.BLOB_CONTAINER,
            blob_name=f"{current_user.user_id}/{filename}",  # Add user_id as prefix
            account_key=settings.BLOB_KEY,
            permission=BlobSasPermissions(write=True),
            expiry=datetime.utcnow() + timedelta(minutes=10),
        )
        
        url = f"https://{settings.BLOB_ACCOUNT_NAME}.blob.core.windows.net/{settings.BLOB_CONTAINER}/{current_user.user_id}/{filename}?{sas_token}"
        
        print(f"Upload URL generated for user {current_user.email_id}: {filename}")
        return {
            "upload_url": url,
            "expires_in": 600,  # 10 minutes in seconds
            "filename": filename,
            "user_id": current_user.user_id
        }
    except Exception as e:
        print(f"Error generating upload URL: {e}")
        return {"error": "Failed to generate upload URL"}


@upload_router.post("/upload-status", response_model=UploadStatusResponse)
async def upload_status(upload_data: UploadStatusRequest):
    """
    Store upload status information in the file_metadata table
    Content-Type: application/json
    """
    try:
        # Prepare the document to insert into MongoDB file_metadata table
        upload_doc = {
            "userId": upload_data.userId,
            "filename": upload_data.filename,
            "file_url": upload_data.file_url,
            "status": upload_data.status,
            "upload_timestamp": upload_data.upload_timestamp,
            "created_at": datetime.utcnow()  # Add server timestamp
        }
        
        # Insert the upload status into MongoDB file_metadata table
        result = await mongo.insert_one("file_metadata", upload_doc)
        
        if result.get("status"):
            logger.info(f"File metadata saved for user {upload_data.userId}: {upload_data.filename}")
            return UploadStatusResponse(
                success=True,
                message="Upload status saved successfully",
                upload_id=str(upload_data.userId)  # You could use MongoDB's ObjectId here
            )
        else:
            logger.error(f"Failed to save file metadata for user {upload_data.userId}")
            raise HTTPException(status_code=500, detail="Failed to save file metadata")
            
    except Exception as e:
        logger.error(f"Error saving file metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")