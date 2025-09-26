import httpx
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.config.settings import settings
from src.config.logging_config import get_logger, log_function_call

# Get logger for this module
logger = get_logger(__name__)
from src.db.mongo_db import mongo


class VitalsExtractionError(Exception):
    """Custom exception for vitals extraction errors"""
    pass


class VitalsStandardizationUtil:
    """Utility class for extracting and standardizing vitals from medical documents"""
    
    def __init__(self, api_base_url: str = settings.OCR_BASE_URL):
        self.api_base_url = api_base_url
        self.extract_vitals_endpoint = f"{api_base_url}/openai/extract-vitals"
    
    
    async def extract_vitals_from_blob(self, blob_path: str) -> Dict[str, Any]:
        """
        Call external API to extract vitals from a blob file
        
        Args:
            blob_path: Path to the blob file (e.g., "1/sample_file.pdf")
            
        Returns:
            Dict containing the API response with extracted vitals
            
        Raises:
            VitalsExtractionError: If API call fails or returns invalid response
        """
        try:
            payload = {"blob_path": blob_path}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.debug("Calling external vitals extraction API")
                response = await client.post(
                    self.extract_vitals_endpoint,
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                
                if response.status_code == 200:
                    api_response = response.json()
                    logger.info(f"Successfully extracted vitals from blob: {blob_path}")
                    return api_response
                else:
                    error_msg = f"API call failed with status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise VitalsExtractionError(error_msg)
                    
        except httpx.RequestError as e:
            error_msg = f"Network error during vitals extraction: {str(e)}"
            logger.error(error_msg)
            raise VitalsExtractionError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from vitals extraction API: {str(e)}"
            logger.error(error_msg)
            raise VitalsExtractionError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during vitals extraction: {str(e)}"
            logger.error(error_msg)
            raise VitalsExtractionError(error_msg)
    
    async def transform_vitals_to_schema(self, api_response: Dict[str, Any], user_id: str, report_id: str, document_id: int) -> Dict[str, Any]:
        """
        Transform API response to match user_vitals collection schema
        
        Args:
            api_response: Response from the vitals extraction API
            user_id: ID of the user who uploaded the document
            report_id: ID of the report/document
            document_id: Sequential document ID from file_metadata
            
        Returns:
            Dict formatted according to user_vitals schema
        """
        try:
            # Extract vitals array from API response
            vitals_list = api_response.get("vital_extraction", {}).get("vitals", [])
            
            # Transform array format to object format required by schema
            vitals_dict = {}
            current_timestamp = datetime.utcnow().isoformat() + "Z"
            
            for vital in vitals_list:
                # Use lowercase name with underscores as key (standardized naming)
                vital_key = vital.get("name", "").lower().replace(" ", "_").replace("%", "percent")
                
                # Clean up the key to be more standardized
                vital_key = self._standardize_vital_name(vital_key)
                
                if vital_key:  # Only add if we have a valid key
                    vitals_dict[vital_key] = {
                        "value": vital.get("value", ""),
                        "unit": vital.get("unit", ""),
                        "timestamp": current_timestamp,
                        "reference_range": vital.get("reference_range", ""),
                        "status": vital.get("status", ""),
                        "original_name": vital.get("name", "")  # Keep original name for reference
                    }
            
            # Create the final document according to schema
            user_vitals_doc = {
                "document_id": document_id,
                "user_id": user_id,
                "report_id": report_id,
                "uploaded_at": current_timestamp,
                "vitals": vitals_dict,
                "source": "pdf_upload",
                "metadata": {
                    "filename": api_response.get("filename", ""),
                    "container_name": api_response.get("container_name", ""),
                    "blob_path": api_response.get("blob_path", ""),
                    "text_character_count": api_response.get("text_character_count", 0),
                    "total_vitals_found": api_response.get("vital_extraction", {}).get("total_vitals_found", 0),
                    "extraction_method": api_response.get("vital_extraction", {}).get("extraction_method", ""),
                    "extraction_status": api_response.get("vital_extraction", {}).get("extraction_status", ""),
                    "token_usage": api_response.get("vital_extraction", {}).get("token_usage", {})
                }
            }
            
            logger.info(f"Transformed {len(vitals_dict)} vitals for user {user_id}")
            return user_vitals_doc
            
        except Exception as e:
            error_msg = f"Error transforming vitals data: {str(e)}"
            logger.error(error_msg)
            raise VitalsExtractionError(error_msg)
    
    def _standardize_vital_name(self, vital_name: str) -> str:
        """
        Standardize vital names to consistent format
        
        Args:
            vital_name: Original vital name
            
        Returns:
            Standardized vital name
        """
        # Dictionary for common vital name mappings
        name_mappings = {
            "haemoglobin": "hemoglobin",
            "rbc_count": "red_blood_cell_count",
            "total_wbc_count": "white_blood_cell_count",
            "neutrophil_percent": "neutrophil_percentage",
            "lymphocyte_percent": "lymphocyte_percentage",
            "eosinophil_percent": "eosinophil_percentage",
            "monocyte": "monocyte_percentage",
            "basophil_percent": "basophil_percentage",
            "platelet_count": "platelet_count",
            "hct": "hematocrit",
            "mch": "mean_corpuscular_hemoglobin",
            "mchc": "mean_corpuscular_hemoglobin_concentration",
            "mcv": "mean_corpuscular_volume",
            "rdw": "red_cell_distribution_width"
        }
        
        return name_mappings.get(vital_name, vital_name)
    
    async def store_vitals_in_db(self, vitals_doc: Dict[str, Any]) -> Optional[str]:
        """
        Store vitals document in user_vitals collection
        
        Args:
            vitals_doc: Document to store in user_vitals collection
            
        Returns:
            String ID of the inserted document, or None if failed
            
        Raises:
            VitalsExtractionError: If database operation fails
        """
        try:
            result = await mongo.insert_one("user_vitals", vitals_doc)
            
            if result.get("status"):
                inserted_id = str(result.get("inserted_id", ""))
                logger.info(f"Successfully stored vitals for user {vitals_doc.get('user_id')} with ID: {inserted_id}")
                return inserted_id
            else:
                error_msg = "Failed to insert vitals document into database"
                logger.error(error_msg)
                raise VitalsExtractionError(error_msg)
                
        except Exception as e:
            error_msg = f"Database error while storing vitals: {str(e)}"
            logger.error(error_msg)
            raise VitalsExtractionError(error_msg)
    
    async def process_document_vitals(self, blob_path: str, user_id: str, document_id: int, report_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete flow: Extract vitals from document, transform, and store in database
        
        Args:
            blob_path: Path to the blob file
            user_id: ID of the user who uploaded the document
            document_id: Sequential document ID from file_metadata
            report_id: Optional report ID (auto-generated if not provided)
            
        Returns:
            Dict containing processing results and stored document ID
            
        Raises:
            VitalsExtractionError: If any step in the process fails
        """
        try:
            # Generate report ID if not provided
            if not report_id:
                report_id = f"rpt_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            # Step 1: Extract vitals from blob
            logger.info(f"Starting vitals extraction for blob: {blob_path}")
            api_response = await self.extract_vitals_from_blob(blob_path)
            
            # Step 2: Transform to schema format
            logger.info(f"Transforming vitals data for user: {user_id}")
            vitals_doc = await self.transform_vitals_to_schema(api_response, user_id, report_id, document_id)
            
            # Step 3: Store in database
            logger.info(f"Storing vitals in database for user: {user_id}")
            document_id = await self.store_vitals_in_db(vitals_doc)
            
            # Return processing summary
            result = {
                "success": True,
                "document_id": vitals_doc.get("document_id"),  # Return the actual document_id from vitals_doc
                "user_id": user_id,
                "report_id": report_id,
                "blob_path": blob_path,
                "vitals_count": len(vitals_doc.get("vitals", {})),
                "processing_timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"Successfully completed vitals processing for user {user_id}")
            return result
            
        except VitalsExtractionError:
            # Re-raise known errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error during vitals processing: {str(e)}"
            logger.error(error_msg)
            raise VitalsExtractionError(error_msg)


# Convenience functions for easy usage
async def extract_and_store_vitals(blob_path: str, user_id: str, document_id: int, report_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to extract and store vitals in one call
    
    Args:
        blob_path: Path to the blob file
        user_id: ID of the user who uploaded the document
        document_id: Sequential document ID from file_metadata
        report_id: Optional report ID
        
    Returns:
        Processing results
    """
    logger.info(f"Processing document vitals: blob_path={blob_path}, user_id={user_id}, document_id={document_id}")
    util = VitalsStandardizationUtil()
    return await util.process_document_vitals(blob_path, user_id, document_id, report_id)


async def extract_vitals_only(blob_path: str) -> Dict[str, Any]:
    """
    Convenience function to only extract vitals without storing
    
    Args:
        blob_path: Path to the blob file
        
    Returns:
        Raw API response
    """
    util = VitalsStandardizationUtil()
    return await util.extract_vitals_from_blob(blob_path)
