from typing import Dict, List, Any
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta

from azure.storage.blob import generate_blob_sas, BlobSasPermissions

from src.config.settings import settings
from src.config.logging_config import get_logger, log_api_request, log_api_response, log_database_operation

# Get logger for this module
logger = get_logger(__name__)
from src.db.mongo_db import mongo
from src.models.User_Model import (
    UserInDB, PaginationQuery, PaginationInfo, 
    DocumentResponse, GetDocumentsResponse,
    VitalData, VitalsMetadata, VitalsResponse, GetVitalsResponse,
    SignedUrlRequest, SignedUrlResponse
)
from src.utils.auth_dependencies import get_current_user

reports_router = APIRouter()


@reports_router.get("/get_documents", response_model=GetDocumentsResponse)
async def get_documents(
    page: int = Query(default=1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of items per page"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get paginated documents for the current user from file_metadata collection
    """
    try:
        # Calculate pagination parameters
        skip = (page - 1) * limit
        
        # Query filter for current user
        query_filter = {"userId": current_user.user_id, "status": "uploaded"}
        
        # Get total count of documents for the user
        total_count = await mongo.count_documents("file_metadata", query_filter)
        
        if total_count == 0:
            # Return empty result with proper pagination info
            pagination_info = PaginationInfo(
                current_page=page,
                per_page=limit,
                total_items=0,
                total_pages=0,
                has_next=False,
                has_prev=False
            )
            
            return GetDocumentsResponse(
                success=True,
                message="No documents found for user",
                documents=[],
                pagination=pagination_info
            )
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / limit)
        has_next = page < total_pages
        has_prev = page > 1
        
        # Query documents with pagination and sorting (most recent first)
        sort_criteria = [("created_at", -1)]  # Sort by created_at descending
        documents = await mongo.fetch_many(
            collection="file_metadata",
            query=query_filter,
            skip=skip,
            limit=limit,
            sort=sort_criteria
        )
        
        # Transform documents to response format
        document_responses = []
        for doc in documents:
            # Handle potential missing fields gracefully
            document_response = DocumentResponse(
                userId=doc.get("userId"),
                document_id=doc.get("document_id"),
                original_filename=doc.get("original_filename"),  # Include original filename
                filename=doc.get("filename", ""),
                file_url=doc.get("file_url", ""),
                blob_path=doc.get("blob_path"),  # Include blob_path
                status=doc.get("status", "unknown"),
                upload_timestamp=doc.get("upload_timestamp", datetime.utcnow()),
                created_at=doc.get("created_at", datetime.utcnow()),
                file_size=doc.get("file_size"),
                content_type=doc.get("content_type"),
                # Include vitals extraction fields for frontend handling
                vital_extracted=doc.get("vital_extracted"),
                vitals_count=doc.get("vitals_count"),
                vitals_processing_status=doc.get("vitals_processing_status"),
                vitals_updated_at=doc.get("vitals_updated_at"),
                vitals_error=doc.get("vitals_error")
            )
            document_responses.append(document_response)
        
        # Create pagination info
        pagination_info = PaginationInfo(
            current_page=page,
            per_page=limit,
            total_items=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        logger.info(f"Retrieved {len(document_responses)} documents for user {current_user.user_id} (page {page}/{total_pages})")
        
        return GetDocumentsResponse(
            success=True,
            message=f"Successfully retrieved {len(document_responses)} documents",
            documents=document_responses,
            pagination=pagination_info
        )
        
    except Exception as e:
        logger.error(f"Error retrieving documents for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@reports_router.get("/get_documents/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: int,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get a specific document by document_id for the current user
    """
    try:
        # Query for the specific document belonging to the current user
        query_filter = {
            "userId": current_user.user_id,
            "document_id": document_id
        }
        
        document = await mongo.fetch_one("file_metadata", query_filter)
        logger.debug(f"Fetched document for user {current_user.user_id}, document_id {document_id}")
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found for user"
            )
        
        # Transform to response format
        document_response = DocumentResponse(
            userId=document.get("userId"),
            document_id=document.get("document_id"),
            original_filename=document.get("original_filename"),  # Include original filename
            filename=document.get("filename", ""),
            file_url=document.get("file_url", ""),
            blob_path=document.get("blob_path"),  # Include blob_path
            status=document.get("status", "unknown"),
            upload_timestamp=document.get("upload_timestamp", datetime.utcnow()),
            created_at=document.get("created_at", datetime.utcnow()),
            file_size=document.get("file_size"),
            content_type=document.get("content_type"),
            # Include vitals extraction fields for frontend handling
            vital_extracted=document.get("vital_extracted"),
            vitals_count=document.get("vitals_count"),
            vitals_processing_status=document.get("vitals_processing_status"),
            vitals_updated_at=document.get("vitals_updated_at"),
            vitals_error=document.get("vitals_error")
        )
        
        logger.info(f"Retrieved document {document_id} for user {current_user.user_id}")
        return document_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {document_id} for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@reports_router.get("/get_vitals/{document_id}", response_model=GetVitalsResponse)
async def get_vitals(
    document_id: int,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get vitals data for a specific document_id from user_vitals collection
    """
    try:
        # Query for vitals belonging to the current user and specific document_id
        query_filter = {
            "user_id": current_user.user_id,  # user_id is stored as string in user_vitals
            "document_id": document_id
        }
        
        vitals_doc = await mongo.fetch_one("user_vitals", query_filter)
        logger.debug(f"Fetched vitals document for user {current_user.user_id}, document_id {document_id}")
        if not vitals_doc:
            return GetVitalsResponse(
                success=False,
                message=f"No vitals found for document ID {document_id}",
                vitals_data=None
            )
        
        # Transform vitals data to response format
        vitals_dict = {}
        raw_vitals = vitals_doc.get("vitals", {})
        logger.debug(f"Retrieved {len(raw_vitals)} vitals for document {document_id}")
        # for vital_name, vital_info in raw_vitals.items():
        #     vitals_dict[vital_name] = VitalData(
        #         value=vital_info.get("value", ""),
        #         unit=vital_info.get("unit", ""),
        #         timestamp=vital_info.get("timestamp", ""),
        #         reference_range=vital_info.get("reference_range"),
        #         status=vital_info.get("status"),
        #         original_name=vital_info.get("original_name")
        #     )
        #
        # # Transform metadata if present
        # metadata = None
        # raw_metadata = vitals_doc.get("metadata", {})
        # if raw_metadata:
        #     metadata = VitalsMetadata(
        #         filename=raw_metadata.get("filename"),
        #         container_name=raw_metadata.get("container_name"),
        #         blob_path=raw_metadata.get("blob_path"),
        #         text_character_count=raw_metadata.get("text_character_count"),
        #         total_vitals_found=raw_metadata.get("total_vitals_found"),
        #         extraction_method=raw_metadata.get("extraction_method"),
        #         extraction_status=raw_metadata.get("extraction_status"),
        #         token_usage=raw_metadata.get("token_usage")
        #     )
        #
        # # Create response
        # vitals_response = VitalsResponse(
        #     document_id=vitals_doc.get("document_id"),
        #     user_id=vitals_doc.get("user_id"),
        #     report_id=vitals_doc.get("report_id", ""),
        #     uploaded_at=vitals_doc.get("uploaded_at", ""),
        #     vitals=vitals_dict,
        #     source=vitals_doc.get("source"),
        #     metadata=metadata
        # )
        #
        # logger.info(f"Retrieved vitals for document {document_id}, user {current_user.user_id}: {len(vitals_dict)} vitals found")
        # return raw_vitals
        return GetVitalsResponse(
            success=True,
            message=f"Successfully retrieved vitals for document {document_id}",
            vitals_data=raw_vitals
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vitals for document {document_id}, user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve vitals: {str(e)}"
        )


@reports_router.post("/get-signed-url", response_model=SignedUrlResponse)
async def get_signed_url(
    request: SignedUrlRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a signed URL for blob file access
    """
    try:
        # Validate blob path format - should include user_id prefix for security
        blob_path = request.blob_path.strip()
        if not blob_path:
            raise HTTPException(
                status_code=400,
                detail="Blob path cannot be empty"
            )
        
        # Security check: ensure the blob path starts with the user's ID
        # This prevents users from accessing files that don't belong to them
        user_prefix = f"{current_user.user_id}/"
        if not blob_path.startswith(user_prefix):
            # If it doesn't start with user_id, prepend it
            # Assume the path is document_id/filename format and prepend user_id
            blob_path = f"{user_prefix}{blob_path}"
        
        # Validate the path structure: should be user_id/document_id/filename
        path_parts = blob_path.split('/')
        if len(path_parts) < 3:
            raise HTTPException(
                status_code=400,
                detail="Invalid blob path format. Expected: user_id/document_id/filename"
            )
        
        # Generate SAS token for read access
        sas_token = generate_blob_sas(
            account_name=settings.BLOB_ACCOUNT_NAME,
            container_name=settings.BLOB_CONTAINER,
            blob_name=blob_path,
            account_key=settings.BLOB_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1),  # 1 hour expiration
        )
        
        # Construct the full signed URL
        signed_url = f"https://{settings.BLOB_ACCOUNT_NAME}.blob.core.windows.net/{settings.BLOB_CONTAINER}/{blob_path}?{sas_token}"
        
        logger.info(f"Generated signed URL for user {current_user.user_id}, blob: {blob_path}")
        
        return SignedUrlResponse(
            success=True,
            message="Signed URL generated successfully",
            signed_url=signed_url,
            expires_in=3600  # 1 hour in seconds
        )
        
    except Exception as e:
        logger.error(f"Error generating signed URL for user {current_user.user_id}, blob {request.blob_path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate signed URL: {str(e)}"
        )
