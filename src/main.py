import uvicorn
import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.db.mongo_db import MongoConnect, mongo
from src.routers.v1.upload_router import upload_router
from src.routers.v1.user_router import user_router
from src.config.settings import settings, logger

app = FastAPI()
# mongo = MongoConnect()


# Configure CORS origins
def get_cors_origins():
    """Get CORS origins based on environment"""
    # Default development origins for React-Vite
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
    
    # Get additional origins from environment variable
    env_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    env_origins = [origin.strip() for origin in env_origins if origin.strip()]
    
    # Combine dev and environment origins
    all_origins = dev_origins + env_origins
    
    # In production, you might want to be more restrictive
    if not settings.debug:
        # You can add production-specific logic here
        pass
    
    return all_origins

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

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Ok"}

@app.on_event("startup")
async def startup_db():
    await mongo.connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db():
    await mongo.close_mongo_connection()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


