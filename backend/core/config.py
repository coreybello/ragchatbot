"""
Configuration management for RAG Demo
Handles environment variables and application settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./data/ragdemo.db", env="DATABASE_URL")
    chroma_persist_dir: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIR")
    
    # LLM Configuration
    model_path: str = Field(default="./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf", env="MODEL_PATH")
    default_temperature: float = Field(default=0.7, env="DEFAULT_TEMPERATURE")
    default_top_p: float = Field(default=1.0, env="DEFAULT_TOP_P")
    
    # Authentication
    jwt_secret: str = Field(default="your-secret-key-here-generate-with-openssl-rand-hex-32", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=1, env="JWT_EXPIRATION_HOURS")
    
    # Admin Configuration
    admin_password_hash: str = Field(default="$2b$12$your-bcrypt-hash-here", env="ADMIN_PASSWORD_HASH")
    
    # Application Settings
    max_upload_size_mb: int = Field(default=50, env="MAX_UPLOAD_SIZE_MB")
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    suggestion_count: int = Field(default=4, env="SUGGESTION_COUNT")
    streaming_chunk_size: int = Field(default=10, env="STREAMING_CHUNK_SIZE")
    
    # Directories
    image_dir: str = Field(default="./data/images", env="IMAGE_DIR")
    pdf_dir: str = Field(default="./data/pdfs", env="PDF_DIR")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Performance
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()

def ensure_directories():
    """Ensure all required directories exist"""
    settings = get_settings()
    
    directories = [
        settings.image_dir,
        settings.pdf_dir,
        "./data/chunks",
        settings.chroma_persist_dir,
        "./models",
        "./prompts"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Initialize directories on import
ensure_directories()