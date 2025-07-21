#!/usr/bin/env python3
"""
Simple test script for core components without ML dependencies
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test that core modules can be imported"""
    print("🔍 Testing core module imports...")
    
    try:
        from backend.models.database import init_db
        print("   ✅ Database models import successful")
        
        from backend.core.config import get_settings
        print("   ✅ Configuration system import successful")
        
        from backend.utils.auth import get_password_hash, verify_password
        print("   ✅ Authentication utilities import successful")
        
        from backend.api.main import app
        print("   ✅ FastAPI app import successful")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("🔍 Testing database setup...")
    
    try:
        from backend.models.database import init_db, SessionLocal, Config
        
        # Initialize database
        init_db()
        print("   ✅ Database initialization successful")
        
        # Test database connection
        db = SessionLocal()
        try:
            configs = db.query(Config).all()
            print(f"   ✅ Database connection successful ({len(configs)} config items)")
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

def test_config():
    """Test configuration system"""
    print("🔍 Testing configuration system...")
    
    try:
        from backend.core.config import get_settings, ensure_directories
        
        settings = get_settings()
        print(f"   ✅ Settings loaded: {settings.database_url}")
        
        ensure_directories()
        print("   ✅ Directories created")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_auth():
    """Test authentication system"""
    print("🔍 Testing authentication system...")
    
    try:
        from backend.utils.auth import get_password_hash, verify_password, create_access_token
        
        # Test password hashing
        password = "test123"
        hashed = get_password_hash(password)
        print("   ✅ Password hashing successful")
        
        # Test password verification
        is_valid = verify_password(password, hashed)
        print(f"   ✅ Password verification: {is_valid}")
        
        # Test JWT token creation
        token = create_access_token({"sub": "admin"})
        print("   ✅ JWT token creation successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False

def test_directory_structure():
    """Test that all required directories exist"""
    print("🔍 Testing directory structure...")
    
    required_dirs = [
        "backend/api",
        "backend/core", 
        "backend/models",
        "backend/utils",
        "frontend/src",
        "data",
        "scripts"
    ]
    
    try:
        for directory in required_dirs:
            if os.path.exists(directory):
                print(f"   ✅ {directory} exists")
            else:
                print(f"   ❌ {directory} missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"   ❌ Directory structure test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🧪 RAG Demo Basic System Tests")
    print("=" * 50)
    
    tests = [
        ("Core Imports", test_imports),
        ("Directory Structure", test_directory_structure),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Authentication", test_auth)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\\n🔬 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    print("\\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\\n🎉 All basic tests passed! Core system is ready.")
        print("\\n📋 Next steps:")
        print("1. Install ML dependencies: pip install chromadb sentence-transformers llama-cpp-python PyMuPDF")
        print("2. Download Mistral 7B model")
        print("3. Start backend: uvicorn backend.api.main:app --reload")
        print("4. Build frontend: cd frontend && npm install && npm start")
        return 0
    else:
        print("\\n⚠️  Some tests failed. Check configuration and dependencies.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)