"""
Database models and initialization for RAG Demo
Using SQLAlchemy with SQLite for simplicity
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import os

from backend.core.config import get_settings

settings = get_settings()

# Create SQLite engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class Query(Base):
    """Query history and metrics table"""
    __tablename__ = "queries"
    
    id = Column(String, primary_key=True)
    timestamp = Column(Integer, nullable=False)
    query = Column(Text, nullable=False)
    response_content = Column(Text, nullable=False)
    response_sources = Column(Text)  # JSON string
    response_images = Column(Text)   # JSON string  
    response_suggestions = Column(Text)  # JSON string
    rating = Column(String)  # 'good', 'bad', or NULL
    response_time_ms = Column(Integer)
    chunks_retrieved = Column(Integer)

class Document(Base):
    """Document metadata table"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    upload_date = Column(String, nullable=False)
    chunks_count = Column(Integer, nullable=False)
    images_count = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

class Config(Base):
    """System configuration table"""
    __tablename__ = "config"
    
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(String, nullable=False)

class DailyMetrics(Base):
    """Daily metrics for dashboard"""
    __tablename__ = "daily_metrics"
    
    date = Column(String, primary_key=True)
    total_queries = Column(Integer, default=0)
    good_ratings = Column(Integer, default=0)
    bad_ratings = Column(Integer, default=0)
    avg_response_time_ms = Column(Integer)
    unique_users = Column(Integer, default=0)

def init_db():
    """Initialize database with tables and default data"""
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session for initial data
    session = SessionLocal()
    
    try:
        # Add default configuration if not exists
        default_configs = [
            ("system_prompt", "You are an IT support assistant. Answer using only the provided documentation. Include images using markdown: ![description](filename)"),
            ("chunk_size", "512"),
            ("chunk_overlap", "50"),
            ("temperature", "0.7"),
            ("top_p", "1.0")
        ]
        
        for key, value in default_configs:
            existing = session.query(Config).filter(Config.key == key).first()
            if not existing:
                config_item = Config(
                    key=key,
                    value=value,
                    updated_at=datetime.now().isoformat()
                )
                session.add(config_item)
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_db():
    """Dependency function to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_config_value(db, key: str, default: str = None):
    """Get configuration value from database"""
    config_item = db.query(Config).filter(Config.key == key).first()
    return config_item.value if config_item else default

def update_config_value(db, key: str, value: str):
    """Update configuration value in database"""
    config_item = db.query(Config).filter(Config.key == key).first()
    if config_item:
        config_item.value = value
        config_item.updated_at = datetime.now().isoformat()
    else:
        config_item = Config(
            key=key,
            value=value,
            updated_at=datetime.now().isoformat()
        )
        db.add(config_item)
    db.commit()