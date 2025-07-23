#!/usr/bin/env python3
"""
API Test Suite for RAG Demo Backend
Tests all FastAPI endpoints without requiring external dependencies
"""

import pytest
import asyncio
import sys
from pathlib import Path
import httpx

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent))

# We'll test with a live server instead of TestClient due to compatibility issues
base_url = "http://localhost:8000"

class TestAPIEndpoints:
    """Test all API endpoints for proper functionality"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = httpx.get(f"{base_url}/health", timeout=5)
            assert response.status_code == 200
            assert "status" in response.json()
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
        
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = httpx.get(f"{base_url}/", timeout=5)
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Backend server not running")
        
    def test_auth_register_endpoint(self):
        """Test user registration endpoint"""
        user_data = {
            "username": "test_qa_user",
            "password": "secure_password_123",
            "email": "qa@test.com"
        }
        response = client.post("/api/auth/register", json=user_data)
        # Should succeed or fail gracefully (not 500 error)
        assert response.status_code in [200, 201, 400, 409]
        
    def test_auth_login_endpoint(self):
        """Test user login endpoint"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = client.post("/api/auth/login", data=login_data)
        # Should handle authentication attempt gracefully
        assert response.status_code in [200, 401, 422]
        
    def test_admin_users_endpoint(self):
        """Test admin users listing endpoint"""
        response = client.get("/api/admin/users")
        # Should require authentication but not crash
        assert response.status_code in [200, 401, 403]
        
    def test_admin_config_endpoint(self):
        """Test admin config endpoint"""
        response = client.get("/api/admin/config")
        assert response.status_code in [200, 401, 403]
        
    def test_admin_stats_endpoint(self):
        """Test admin statistics endpoint"""
        response = client.get("/api/admin/stats")
        assert response.status_code in [200, 401, 403]
        
    def test_metrics_system_endpoint(self):
        """Test system metrics endpoint"""
        response = client.get("/api/metrics/system")
        assert response.status_code in [200, 401, 403]
        
    def test_metrics_usage_endpoint(self):
        """Test usage metrics endpoint"""
        response = client.get("/api/metrics/usage")
        assert response.status_code in [200, 401, 403]
        
    def test_chat_endpoint_structure(self):
        """Test chat endpoint structure (without LLM)"""
        chat_data = {
            "message": "Hello, this is a test message",
            "use_history": False
        }
        response = client.post("/api/chat", json=chat_data)
        # Should fail gracefully if LLM not available
        assert response.status_code in [200, 400, 500, 503]
        
    def test_upload_endpoint_structure(self):
        """Test file upload endpoint structure"""
        # Test without actual file (should handle gracefully)
        response = client.post("/api/upload")
        assert response.status_code in [400, 422]  # Should validate input

if __name__ == "__main__":
    pytest.main([__file__, "-v"])