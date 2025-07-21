"""
FastAPI main application entry point for RAG Demo
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from backend.core.config import get_settings
from backend.models.database import init_db
from backend.api import auth, chat, admin, metrics, analysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting RAG Demo backend...")
    settings = get_settings()
    
    # Initialize database
    init_db()
    logger.info("✅ Database initialized")
    
    # Initialize vector store
    # Vector store initialization will be handled by core modules
    logger.info("✅ Vector store ready")
    
    # Initialize LLM
    # LLM initialization will be handled by llm_client module
    logger.info("✅ LLM ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down RAG Demo backend...")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="RAG Demo API",
    description="Retrieval-Augmented Generation chatbot backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for images
if not os.path.exists("./data/images"):
    os.makedirs("./data/images", exist_ok=True)
    
app.mount("/images", StaticFiles(directory="./data/images"), name="images")

# Include API routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RAG Demo API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2023-12-01T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )