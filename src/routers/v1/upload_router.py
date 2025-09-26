from datetime import datetime, timedelta

from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from fastapi import APIRouter, Form, Depends, HTTPException, UploadFile

from src.config.settings import settings
from src.config.logging_config import get_logger, log_api_request, log_api_response, log_function_call

# Get logger for this module
logger = get_logger(__name__)
from src.models.User_Model import UserInDB, UploadStatusRequest, UploadStatusResponse
from src.utils.auth_dependencies import get_current_user
from src.utils.util import sanitize_filename
from src.db.mongo_db import mongo


async def get_next_document_id() -> int:
    """
    Generate next auto-incremental document_id using MongoDB counter collection
    
    Returns:
        Next document ID as integer
    """
    try:
        # Check if counter document exists
        counter_doc = await mongo.fetch_one("counters", {"_id": "file_metadata_document_id"})
        
        if counter_doc:
            # Increment existing counter
            new_value = counter_doc.get("sequence_value", 0) + 1
            await mongo.update_one(
                "counters",
                {"_id": "file_metadata_document_id"},
                {"$set": {"sequence_value": new_value}}
            )
            logger.info(f"Generated next document_id: {new_value}")
            return new_value
        else:
            # Create initial counter document
            initial_doc = {
                "_id": "file_metadata_document_id",
                "sequence_value": 1
            }
            await mongo.insert_one("counters", initial_doc)
            logger.info("Created initial counter, document_id: 1")
            return 1
            
    except Exception as e:
        # Fallback: use timestamp-based ID if any error occurs
        fallback_id = int(datetime.utcnow().timestamp())
        logger.error(f"Error generating document_id, using fallback {fallback_id}: {e}")
        return fallback_id

upload_router = APIRouter()

# Initialize blob service client
blob_service_client = BlobServiceClient(
    account_url=f"https://{settings.BLOB_ACCOUNT_NAME}.blob.core.windows.net",
    credential=settings.BLOB_KEY
)


@upload_router.post("/generate-upload-url")
async def generate_upload_url(
    filename: str = Form(...), 
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a SAS token for blob upload (Protected endpoint)
    """
    try:
        # Sanitize filename to ensure only lowercase alphabetical characters
        sanitized_filename = sanitize_filename(filename)
        logger.info(f"Original filename: '{filename}' -> Sanitized: '{sanitized_filename}' for user {current_user.user_id}")
        
        # Generate document_id first
        document_id = await get_next_document_id()
        logger.info(f"Generated document_id: {document_id} for upload URL generation, user {current_user.user_id}")
        
        # Create blob path with new structure: user_id/document_id/sanitized_filename
        blob_name = f"{current_user.user_id}/{document_id}/{sanitized_filename}"
        
        sas_token = generate_blob_sas(
            account_name=settings.BLOB_ACCOUNT_NAME,
            container_name=settings.BLOB_CONTAINER,
            blob_name=blob_name,
            account_key=settings.BLOB_KEY,
            permission=BlobSasPermissions(write=True),
            expiry=datetime.utcnow() + timedelta(minutes=10),
        )
        
        url = f"https://{settings.BLOB_ACCOUNT_NAME}.blob.core.windows.net/{settings.BLOB_CONTAINER}/{blob_name}?{sas_token}"
        
        logger.info(f"Upload URL generated for user {current_user.email_id}: {sanitized_filename}, document_id: {document_id}")
        return {
            "upload_url": url,
            "expires_in": 600,  # 10 minutes in seconds
            "original_filename": filename,  # Original filename provided
            "sanitized_filename": sanitized_filename,  # Sanitized filename used
            "user_id": current_user.user_id,
            "document_id": document_id,  # Return document_id to client
            "blob_path": blob_name  # Return full blob path for reference
        }
    except Exception as e:
        logger.error(f"Error generating upload URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")


@upload_router.post("/upload-status", response_model=UploadStatusResponse)
async def upload_status(upload_data: UploadStatusRequest):
    """
    Store upload status information in the file_metadata table
    Content-Type: application/json
    """
    try:
        # Sanitize filename to ensure only lowercase alphabetical characters
        sanitized_filename = sanitize_filename(upload_data.filename)
        logger.info(f"Original filename: '{upload_data.filename}' -> Sanitized: '{sanitized_filename}' for upload-status endpoint")
        
        # Generate document_id if not provided
        document_id = upload_data.document_id
        if document_id is None:
            document_id = await get_next_document_id()
            logger.info(f"Generated document_id: {document_id} for upload-status endpoint")
        
        # Extract blob_path from file_url for storage
        # file_url format: https://{account}.blob.core.windows.net/{container}/{blob_path}?{sas}
        blob_path = None
        if upload_data.file_url:
            try:
                # Extract blob path from URL
                url_parts = upload_data.file_url.split('/')
                container_index = url_parts.index(settings.BLOB_CONTAINER)
                if container_index + 1 < len(url_parts):
                    # Get everything after container name, remove query parameters
                    blob_path = '/'.join(url_parts[container_index + 1:]).split('?')[0]
            except (ValueError, IndexError):
                logger.warning(f"Could not extract blob_path from file_url: {upload_data.file_url}")
        
        # Prepare the document to insert into MongoDB file_metadata table
        upload_doc = {
            "userId": upload_data.userId,
            "document_id": document_id,
            "original_filename": upload_data.filename,  # Store original filename
            "filename": sanitized_filename,  # Store sanitized filename
            "file_url": upload_data.file_url,
            "blob_path": blob_path,  # Store extracted blob path
            "status": upload_data.status,
            "upload_timestamp": upload_data.upload_timestamp,
            "created_at": datetime.utcnow(),  # Add server timestamp
            # Initialize vitals extraction fields (these will be updated by background processing)
            "vital_extracted": False,
            "vitals_count": 0,
            "vitals_processing_status": "pending"
        }
        
        # Insert the upload status into MongoDB file_metadata table
        result = await mongo.insert_one("file_metadata", upload_doc)
        
        if result.get("status"):
            logger.info(f"File metadata saved for user {upload_data.userId}: {sanitized_filename} (original: {upload_data.filename})")
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


@upload_router.post("/direct")
async def upload_file_direct(
    file: UploadFile, 
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Direct file upload to blob storage through backend (Protected endpoint)
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Sanitize filename to ensure only lowercase alphabetical characters
        sanitized_filename = sanitize_filename(file.filename)
        logger.info(f"Original filename: '{file.filename}' -> Sanitized: '{sanitized_filename}' for user {current_user.user_id}")
        
        # Generate document_id first for file_metadata
        document_id = await get_next_document_id()
        logger.info(f"Generated document_id: {document_id} for user {current_user.user_id}")
        
        # Generate blob name with new path structure: user_id/document_id/sanitized_filename
        blob_name = f"{current_user.user_id}/{document_id}/{sanitized_filename}"
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=settings.BLOB_CONTAINER, 
            blob=blob_name
        )
        
        # Read file content
        file_content = await file.read()
        
        # Upload file content to blob storage
        blob_client.upload_blob(file_content, overwrite=True)
        logger.info(f"File uploaded successfully for user {current_user.user_id}: {sanitized_filename}")
        
        # Extract vitals first before saving to database (single DB call optimization)
        vital_extracted = False
        vitals_count = 0
        vitals_error = None
        vitals_processing_status = "failed"  # Default to failed
        
        try:
            from src.utils.entity_standardisation_util import extract_and_store_vitals
            logger.info(f"Starting vitals extraction for user {current_user.user_id}, document_id: {document_id}")
            
            vitals_result = await extract_and_store_vitals(
                blob_path=blob_name,  # Format: "1/123/sample_file.pdf"
                user_id=current_user.user_id,
                document_id=document_id  # Pass the document_id from file_metadata
            )
            
            # Check if vitals were successfully extracted
            if vitals_result and vitals_result.get('success', False):
                vitals_count = vitals_result.get('vitals_count', 0)
                vital_extracted = vitals_count > 0  # True only if vitals were actually found
                vitals_processing_status = "completed"
                
                logger.info(f"Vitals extracted and stored: {vitals_count} vitals found for user {current_user.user_id}, document_id: {document_id}")
            else:
                vital_extracted = False
                vitals_count = 0
                vitals_processing_status = "failed"
                vitals_error = "Vitals extraction returned unsuccessful result"
                logger.warning(f"Vitals extraction was unsuccessful for user {current_user.user_id}, document_id: {document_id}")
                
        except Exception as e:
            # Don't fail the upload if vitals extraction fails
            vital_extracted = False
            vitals_count = 0
            vitals_processing_status = "failed"
            vitals_error = str(e)
            logger.error(f"Vitals extraction failed for user {current_user.user_id}: {e}")
        
        # Create upload record with final vitals extraction results (SINGLE DB CALL)
        upload_doc = {
            "userId": current_user.user_id,
            "document_id": document_id,
            "original_filename": file.filename,  # Store original filename
            "filename": sanitized_filename,  # Store sanitized filename
            "file_url": blob_client.url,
            "blob_path": blob_name,  # Store blob path for easy retrieval
            "status": "uploaded",
            "upload_timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "file_size": len(file_content),
            "content_type": file.content_type or "application/octet-stream",
            # Final vitals extraction results
            "vital_extracted": vital_extracted,
            "vitals_count": vitals_count,
            "vitals_processing_status": vitals_processing_status,
            "vitals_updated_at": datetime.utcnow()
        }
        
        # Add error message if present
        if vitals_error:
            upload_doc["vitals_error"] = vitals_error
        
        # Single database insert with complete data
        result = await mongo.insert_one("file_metadata", upload_doc)
        
        if result.get("status"):
            logger.info(f"File metadata saved successfully with vitals results for user {current_user.email_id}: {sanitized_filename} (vitals: {vital_extracted})")
            
            return {
                "success": True,
                "file_url": blob_client.url, 
                "status": "uploaded",
                "original_filename": file.filename,
                "sanitized_filename": sanitized_filename,
                "user_id": current_user.user_id,
                "document_id": document_id,
                "blob_path": blob_name,
                "upload_id": str(result.get("inserted_id", "")),
                # Vitals extraction information for frontend
                "vital_extracted": vital_extracted,
                "vitals_count": vitals_count,
                "vitals_processing_status": vitals_processing_status,
                "vitals_error": vitals_error if vitals_error else None
            }
        else:
            # If database insert failed, we should ideally delete the blob
            logger.error(f"Failed to save file metadata for user {current_user.user_id}")
            raise HTTPException(status_code=500, detail="Failed to save file metadata")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


