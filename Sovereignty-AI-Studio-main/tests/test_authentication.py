import pytest
from httpx import AsyncClient
from backend.app.main import app
from backend.app.core.security import get_password_hash


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url='http://test') as client:
        yield client


@pytest.fixture
def test_user_data():
    """Test user registration data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!@#",
        "full_name": "Test User"
    }


class TestAuthentication:
    """Test suite for authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = await client.post('/api/v1/auth/register', json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "password" not in data  # Password should not be returned
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user_data):
        """Test registration with duplicate username."""
        # Register first user
        await client.post('/api/v1/auth/register', json=test_user_data)
        
        # Try to register with same username but different email
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        response = await client.post('/api/v1/auth/register', json=duplicate_data)
        
        assert response.status_code == 400
        assert "username already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email."""
        # Register first user
        await client.post('/api/v1/auth/register', json=test_user_data)
        
        # Try to register with same email but different username
        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "different_user"
        response = await client.post('/api/v1/auth/register', json=duplicate_data)
        
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client, test_user_data):
        """Test registration with weak password."""
        weak_passwords = [
            "short",  # Too short
            "alllowercase123!",  # No uppercase
            "ALLUPPERCASE123!",  # No lowercase
            "NoNumbers!",  # No digits
            "NoSpecial123",  # No special characters
        ]
        
        for weak_password in weak_passwords:
            data = test_user_data.copy()
            data["password"] = weak_password
            response = await client.post('/api/v1/auth/register', json=data)
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_invalid_username(self, client, test_user_data):
        """Test registration with invalid username format."""
        invalid_usernames = [
            "ab",  # Too short
            "a" * 21,  # Too long
            "user@name",  # Invalid character
            "user name",  # Space
        ]
        
        for invalid_username in invalid_usernames:
            data = test_user_data.copy()
            data["username"] = invalid_username
            response = await client.post('/api/v1/auth/register', json=data)
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user_data):
        """Test successful login."""
        # Register user first
        await client.post('/api/v1/auth/register', json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = await client.post(
            '/api/v1/auth/login',
            data=login_data  # OAuth2PasswordRequestForm expects form data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user_data):
        """Test login with wrong password."""
        # Register user first
        await client.post('/api/v1/auth/register', json=test_user_data)
        
        # Try to login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123!"
        }
        response = await client.post('/api/v1/auth/login', data=login_data)
        
        assert response.status_code == 401
        assert "incorrect username or password" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        login_data = {
            "username": "nonexistent",
            "password": "Password123!"
        }
        response = await client.post('/api/v1/auth/login', data=login_data)
        
        assert response.status_code == 401
        assert "incorrect username or password" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_token_login(self, client, test_user_data):
        """Test login with JSON token endpoint."""
        # Register user first
        await client.post('/api/v1/auth/register', json=test_user_data)
        
        # Login with JSON endpoint
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = await client.post('/api/v1/auth/token', json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without authentication."""
        response = await client.get('/api/v1/users/me')
        assert response.status_code == 403  # Forbidden without auth
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(self, client, test_user_data):
        """Test accessing protected endpoint with valid token."""
        # Register and login
        await client.post('/api/v1/auth/register', json=test_user_data)
        login_response = await client.post(
            '/api/v1/auth/login',
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = await client.get(
            '/api/v1/users/me',
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = await client.get(
            '/api/v1/users/me',
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestInputValidation:
    """Test suite for input validation and sanitization."""
    
    @pytest.mark.asyncio
    async def test_bio_sanitization(self, client, test_user_data):
        """Test that bio field is sanitized against XSS."""
        # Register and login
        await client.post('/api/v1/auth/register', json=test_user_data)
        login_response = await client.post(
            '/api/v1/auth/login',
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Update bio with potentially dangerous content
        update_data = {
            "bio": "<script>alert('XSS')</script>This is my bio"
        }
        response = await client.put(
            '/api/v1/users/me',
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Verify dangerous tags are removed
        assert "<script>" not in data["bio"]
        assert "alert" not in data["bio"]
    
    @pytest.mark.asyncio
    async def test_avatar_url_validation(self, client, test_user_data):
        """Test avatar URL validation."""
        # Register and login
        await client.post('/api/v1/auth/register', json=test_user_data)
        login_response = await client.post(
            '/api/v1/auth/login',
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Try to set invalid avatar URL
        invalid_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "not-a-url"
        ]
        
        for invalid_url in invalid_urls:
            update_data = {"avatar_url": invalid_url}
            response = await client.put(
                '/api/v1/users/me',
                json=update_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 422  # Validation error


class TestRateLimiting:
    """Test suite for rate limiting."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, client):
        """Test that rate limiting is enforced on endpoints."""
        # Make multiple requests to root endpoint (10/minute limit)
        for i in range(11):
            response = await client.get('/')
            if i < 10:
                assert response.status_code == 200
            else:
                # 11th request should be rate limited
                assert response.status_code == 429  # Too Many Requests


class TestSecurityHeaders:
    """Test suite for security headers."""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = await client.get('/health')
        
        # Check for security headers
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers
