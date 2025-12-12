"""
Paket Routing API - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from db.database import init_db, close_db
from routers import ingest, address, routing, health

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Paket Routing API...")
    await init_db()
    logger.info("Database connection initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Paket Routing API...")
    await close_db()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Package Routing & OCR System API
    
    This API provides endpoints for:
    - **Ingest**: Receive OCR text and images from edge devices
    - **Address**: Parse, normalize, and geocode addresses
    - **Routing**: Optimize delivery routes using VRP algorithms
    
    ### Features
    - Real-time OCR processing
    - Indonesian address parsing with RT/RW support
    - Geocoding with caching
    - CVRPTW optimization using OR-Tools
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingest"])
app.include_router(address.router, prefix="/api/v1/address", tags=["Address"])
app.include_router(routing.router, prefix="/api/v1/routes", tags=["Routing"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc) if settings.debug else None}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host if hasattr(settings, 'app_host') else "0.0.0.0",
        port=settings.app_port if hasattr(settings, 'app_port') else 8000,
        reload=settings.debug
    )
