#!/usr/bin/env python3
"""
Database Test Suite for RAG Demo
Tests database models, connections, and CRUD operations
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent))

from backend.models.database import Base, User, Config, Document, ChatMessage, init_db
from backend.utils.auth import get_password_hash

class TestDatabase:
    """Test database functionality"""
    
    @pytest.fixture
    def test_db(self):
        """Create temporary test database"""
        # Create temporary database file
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        # Create engine and session
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield SessionLocal
        
        # Cleanup
        os.unlink(db_path)
    
    def test_database_initialization(self, test_db):
        """Test database table creation"""
        db = test_db()
        try:
            # Check that all tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()
            
            expected_tables = ['users', 'config', 'documents', 'chat_messages']
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
                
        finally:
            db.close()
    
    def test_user_model(self, test_db):
        """Test User model CRUD operations"""
        db = test_db()
        try:
            # Create user
            hashed_password = get_password_hash("test123")
            user = User(
                username="test_user",
                email="test@example.com",
                hashed_password=hashed_password,
                is_admin=False
            )
            db.add(user)
            db.commit()
            
            # Read user
            retrieved_user = db.query(User).filter(User.username == "test_user").first()
            assert retrieved_user is not None
            assert retrieved_user.email == "test@example.com"
            assert retrieved_user.is_admin == False
            
            # Update user
            retrieved_user.is_admin = True
            db.commit()
            
            updated_user = db.query(User).filter(User.username == "test_user").first()
            assert updated_user.is_admin == True
            
            # Delete user
            db.delete(updated_user)
            db.commit()
            
            deleted_user = db.query(User).filter(User.username == "test_user").first()
            assert deleted_user is None
            
        finally:
            db.close()
    
    def test_config_model(self, test_db):
        """Test Config model operations"""
        db = test_db()
        try:
            # Create config
            from datetime import datetime
            config = Config(
                key="test_setting", 
                value="test_value",
                updated_at=datetime.now().isoformat()
            )
            db.add(config)
            db.commit()
            
            # Read config
            retrieved_config = db.query(Config).filter(Config.key == "test_setting").first()
            assert retrieved_config is not None
            assert retrieved_config.value == "test_value"
            
        finally:
            db.close()
    
    def test_document_model(self, test_db):
        """Test Document model operations"""
        db = test_db()
        try:
            # Create document
            document = Document(
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                file_size=1024,
                chunks_count=5,
                processed=True
            )
            db.add(document)
            db.commit()
            
            # Read document
            retrieved_doc = db.query(Document).filter(Document.filename == "test.pdf").first()
            assert retrieved_doc is not None
            assert retrieved_doc.file_size == 1024
            assert retrieved_doc.processed == True
            
        finally:
            db.close()
    
    def test_chat_message_model(self, test_db):
        """Test ChatMessage model operations"""
        db = test_db()
        try:
            # Create user first
            user = User(
                username="chat_user",
                email="chat@example.com",
                hashed_password=get_password_hash("test123")
            )
            db.add(user)
            db.commit()
            
            # Create chat message
            message = ChatMessage(
                user_id=user.id,
                message="Hello, how are you?",
                response="I'm doing well, thank you!",
                response_time=1.5
            )
            db.add(message)
            db.commit()
            
            # Read message
            retrieved_msg = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).first()
            assert retrieved_msg is not None
            assert retrieved_msg.message == "Hello, how are you?"
            assert retrieved_msg.response_time == 1.5
            
        finally:
            db.close()
    
    def test_database_relationships(self, test_db):
        """Test relationships between models"""
        db = test_db()
        try:
            # Create user
            user = User(
                username="rel_user",
                email="rel@example.com", 
                hashed_password=get_password_hash("test123")
            )
            db.add(user)
            db.commit()
            
            # Create multiple chat messages for the user
            for i in range(3):
                message = ChatMessage(
                    user_id=user.id,
                    message=f"Message {i}",
                    response=f"Response {i}",
                    response_time=float(i)
                )
                db.add(message)
            
            db.commit()
            
            # Test relationship
            user_with_messages = db.query(User).filter(User.username == "rel_user").first()
            assert len(user_with_messages.chat_messages) == 3
            
        finally:
            db.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])