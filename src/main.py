import uvicorn
import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.db.mongo_db import MongoConnect, mongo
from src.routers.v1.upload_router import upload_router
from src.routers.v1.user_router import user_router
from src.routers.v1.reports_router import reports_router
from src.config.settings import settings
from src.config.logging_config import get_logger, log_api_request, log_api_response
from src.middleware.logging_middleware import (
    APILoggingMiddleware, 
    PerformanceLoggingMiddleware, 
    SecurityLoggingMiddleware
)

# Get logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title="Swasthasathi Service",
    description="Healthcare Management Service API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# mongo = MongoConnect()


# Configure CORS origins
def get_cors_origins():
    """Get CORS origins based on environment configuration"""
    origins = []
    
    # Get origins from settings (environment variable)
    if settings.CORS_ORIGINS:
        env_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
        origins.extend(env_origins)
    
    # Add default development origins only in debug mode
    if settings.debug:
        dev_origins = [
            "http://localhost:5173",    # Default Vite dev server
            "http://localhost:3000",    # Common React dev server
            "http://localhost:3001",    # Alternative React dev server
            "http://localhost:5174",    # Alternative Vite port
            "http://127.0.0.1:5173",    # Alternative localhost
            "http://127.0.0.1:3000",    # Alternative localhost
            "http://127.0.0.1:3001",    # Alternative localhost
            "http://127.0.0.1:5174",    # Alternative localhost
        ]
        origins.extend(dev_origins)
    
    # If no origins configured and not in debug mode, use restrictive default
    if not origins and not settings.debug:
        logger.warning("No CORS origins configured for production!")
        return []
    
    logger.info(f"CORS origins configured: {origins}")
    return origins

# Add comprehensive logging middleware
app.add_middleware(APILoggingMiddleware)
app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold=2000.0)  # 2 seconds
app.add_middleware(SecurityLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],  # This includes OPTIONS
    allow_headers=["*"],
)

# Custom exception handler for validation errors (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for 422 validation errors that logs the raw request data
    """
    try:
        # Get the raw request body
        body = await request.body()
        raw_body = body.decode('utf-8')
        
        # Log the raw request data
        logger.error(f"🚨 422 Validation Error for {request.method} {request.url}")
        logger.error(f"📥 Raw request body: {raw_body}")
        logger.error(f"📋 Validation errors: {exc.errors()}")
        
        # Try to parse as JSON for better logging
        try:
            json_data = json.loads(raw_body) if raw_body else {}
            logger.error(f"📊 Parsed JSON data: {json.dumps(json_data, indent=2)}")
        except json.JSONDecodeError:
            logger.error(f"📄 Non-JSON body: {raw_body}")
        
        # Return detailed error response
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "message": "Validation failed - check the debug logs for raw request data",
                "debug_info": {
                    "endpoint": str(request.url),
                    "method": request.method,
                    "raw_body_preview": raw_body[:500] + "..." if len(raw_body) > 500 else raw_body,
                    "suggestion": "Check /user/signup-debug endpoint to test your data format"
                }
            }
        )
    except Exception as e:
        logger.error(f"Error in validation exception handler: {e}")
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )

app.include_router(user_router, prefix="/user", tags=["Users"])
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])

@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint with service status"""
    try:
        # Check database connectivity
        db_status = "healthy"
        try:
            await mongo.client.admin.command('ping')
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            logger.error("Database health check failed", extra={"error": str(e)})
        
        health_data = {
            "service": "Swasthasathi Service",
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "components": {
                "database": db_status,
                "api": "healthy"
            }
        }
        
        if db_status == "healthy":
            logger.debug("Health check passed", extra=health_data)
            return health_data
        else:
            logger.warning("Health check failed", extra=health_data)
            raise HTTPException(status_code=503, detail=health_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health check endpoint error", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=503, 
            detail={
                "service": "Swasthasathi Service",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

@app.on_event("startup")
async def startup_db():
    logger.info("Starting Swasthasathi Service application")
    await mongo.connect_to_mongo()
    logger.info("Database connection established successfully")

@app.on_event("shutdown")
async def shutdown_db():
    logger.info("Shutting down Swasthasathi Service application")
    await mongo.close_mongo_connection()
    logger.info("Application shutdown completed")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.debug
    )


