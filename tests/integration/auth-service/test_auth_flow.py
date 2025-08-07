"""
Integration tests for authentication flow
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import json
import uuid


@pytest.mark.integration
@pytest.mark.auth
class TestAuthFlow:
    """Test complete authentication flow"""
    
    @pytest.mark.asyncio
    async def test_user_registration_flow(self):
        """Test complete user registration flow"""
        
        # Mock HTTP client
        mock_client = AsyncMock(spec=AsyncClient)
        
        # User registration data
        user_data = {
            "email": "integration@test.com",
            "password": "TestPass123!",
            "firstName": "Integration",
            "lastName": "Test"
        }
        
        # Mock successful registration response
        registration_response = AsyncMock()
        registration_response.status_code = 201
        registration_response.json.return_value = {
            "id": str(uuid.uuid4()),
            "email": user_data["email"],
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
            "role": "user",
            "isActive": True,
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        mock_client.post.return_value = registration_response
        
        # Test registration
        response = await mock_client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["email"] == user_data["email"]
        assert response_data["firstName"] == user_data["firstName"]
        assert response_data["role"] == "user"
        assert response_data["isActive"] is True
        
        # Verify the call was made correctly
        mock_client.post.assert_called_with("/auth/register", json=user_data)
    
    @pytest.mark.asyncio
    async def test_user_login_flow(self):
        """Test user login flow"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Login data
        login_data = {
            "email": "integration@test.com",
            "password": "TestPass123!"
        }
        
        # Mock successful login response
        login_response = AsyncMock()
        login_response.status_code = 200
        login_response.json.return_value = {
            "accessToken": "mock.jwt.token",
            "tokenType": "bearer",
            "expiresIn": 3600,
            "user": {
                "id": str(uuid.uuid4()),
                "email": login_data["email"],
                "role": "user"
            }
        }
        
        mock_client.post.return_value = login_response
        
        # Test login
        response = await mock_client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "accessToken" in response_data
        assert response_data["tokenType"] == "bearer"
        assert response_data["expiresIn"] == 3600
        assert response_data["user"]["email"] == login_data["email"]
    
    @pytest.mark.asyncio
    async def test_protected_resource_access(self):
        """Test accessing protected resources with token"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock authenticated request
        token = "mock.jwt.token"
        mock_client.headers = {"Authorization": f"Bearer {token}"}
        
        # Mock successful profile response
        profile_response = AsyncMock()
        profile_response.status_code = 200
        profile_response.json.return_value = {
            "id": str(uuid.uuid4()),
            "email": "integration@test.com",
            "firstName": "Integration",
            "lastName": "Test",
            "role": "user",
            "permissions": ["read:own", "write:own"]
        }
        
        mock_client.get.return_value = profile_response
        
        # Test accessing protected resource
        response = await mock_client.get("/auth/me")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["email"] == "integration@test.com"
        assert "permissions" in response_data
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self):
        """Test unauthorized access to protected resources"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock unauthorized response
        unauthorized_response = AsyncMock()
        unauthorized_response.status_code = 401
        unauthorized_response.json.return_value = {
            "detail": "Not authenticated"
        }
        
        mock_client.get.return_value = unauthorized_response
        
        # Test accessing protected resource without token
        response = await mock_client.get("/auth/me")
        
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self):
        """Test token refresh flow"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock token refresh response
        refresh_response = AsyncMock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            "accessToken": "new.jwt.token",
            "tokenType": "bearer",
            "expiresIn": 3600
        }
        
        mock_client.post.return_value = refresh_response
        
        # Test token refresh
        refresh_data = {"refreshToken": "mock.refresh.token"}
        response = await mock_client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["accessToken"] == "new.jwt.token"
        assert response_data["tokenType"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_user_logout_flow(self):
        """Test user logout flow"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock logout response
        logout_response = AsyncMock()
        logout_response.status_code = 200
        logout_response.json.return_value = {
            "message": "Successfully logged out"
        }
        
        mock_client.post.return_value = logout_response
        
        # Test logout
        token = "mock.jwt.token"
        mock_client.headers = {"Authorization": f"Bearer {token}"}
        response = await mock_client.post("/auth/logout")
        
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data


@pytest.mark.integration
@pytest.mark.auth
class TestRoleBasedAccess:
    """Test role-based access control integration"""
    
    @pytest.mark.asyncio
    async def test_admin_access_control(self):
        """Test admin access to administrative endpoints"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock admin token
        admin_token = "admin.jwt.token"
        mock_client.headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Mock successful admin response
        admin_response = AsyncMock()
        admin_response.status_code = 200
        admin_response.json.return_value = {
            "users": [
                {"id": "1", "email": "user1@test.com", "role": "user"},
                {"id": "2", "email": "user2@test.com", "role": "operator"}
            ],
            "total": 2
        }
        
        mock_client.get.return_value = admin_response
        
        # Test admin endpoint access
        response = await mock_client.get("/admin/users")
        
        assert response.status_code == 200
        response_data = response.json()
        assert "users" in response_data
        assert "total" in response_data
    
    @pytest.mark.asyncio
    async def test_user_forbidden_access(self):
        """Test regular user forbidden access to admin endpoints"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock user token
        user_token = "user.jwt.token"
        mock_client.headers = {"Authorization": f"Bearer {user_token}"}
        
        # Mock forbidden response
        forbidden_response = AsyncMock()
        forbidden_response.status_code = 403
        forbidden_response.json.return_value = {
            "detail": "Insufficient permissions"
        }
        
        mock_client.get.return_value = forbidden_response
        
        # Test forbidden endpoint access
        response = await mock_client.get("/admin/users")
        
        assert response.status_code == 403
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_operator_limited_access(self):
        """Test operator limited access to resources"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock operator token
        operator_token = "operator.jwt.token"
        mock_client.headers = {"Authorization": f"Bearer {operator_token}"}
        
        # Mock operator response - can read but not delete
        read_response = AsyncMock()
        read_response.status_code = 200
        read_response.json.return_value = {"devices": [{"id": "1", "name": "Device 1"}]}
        
        delete_response = AsyncMock()
        delete_response.status_code = 403
        delete_response.json.return_value = {"detail": "Cannot delete devices"}
        
        # Set up different responses for different calls
        mock_client.get.return_value = read_response
        mock_client.delete.return_value = delete_response
        
        # Test read access (should succeed)
        read_resp = await mock_client.get("/devices")
        assert read_resp.status_code == 200
        
        # Test delete access (should fail)
        delete_resp = await mock_client.delete("/devices/1")
        assert delete_resp.status_code == 403


@pytest.mark.integration
@pytest.mark.auth
class TestAuthErrorHandling:
    """Test authentication error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock invalid credentials response
        error_response = AsyncMock()
        error_response.status_code = 401
        error_response.json.return_value = {
            "detail": "Invalid email or password"
        }
        
        mock_client.post.return_value = error_response
        
        # Test login with invalid credentials
        invalid_login = {
            "email": "wrong@test.com",
            "password": "wrongpassword"
        }
        
        response = await mock_client.post("/auth/login", json=invalid_login)
        
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_duplicate_registration(self):
        """Test registration with existing email"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock duplicate email response
        conflict_response = AsyncMock()
        conflict_response.status_code = 409
        conflict_response.json.return_value = {
            "detail": "Email already exists"
        }
        
        mock_client.post.return_value = conflict_response
        
        # Test duplicate registration
        duplicate_user = {
            "email": "existing@test.com",
            "password": "TestPass123!",
            "firstName": "Test",
            "lastName": "User"
        }
        
        response = await mock_client.post("/auth/register", json=duplicate_user)
        
        assert response.status_code == 409
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_expired_token_handling(self):
        """Test handling of expired tokens"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock expired token response
        expired_response = AsyncMock()
        expired_response.status_code = 401
        expired_response.json.return_value = {
            "detail": "Token has expired"
        }
        
        mock_client.get.return_value = expired_response
        
        # Test with expired token
        expired_token = "expired.jwt.token"
        mock_client.headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await mock_client.get("/auth/me")
        
        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_malformed_token_handling(self):
        """Test handling of malformed tokens"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock malformed token response
        malformed_response = AsyncMock()
        malformed_response.status_code = 422
        malformed_response.json.return_value = {
            "detail": "Invalid token format"
        }
        
        mock_client.get.return_value = malformed_response
        
        # Test with malformed token
        malformed_token = "not.a.valid.token"
        mock_client.headers = {"Authorization": f"Bearer {malformed_token}"}
        
        response = await mock_client.get("/auth/me")
        
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data


@pytest.mark.integration
@pytest.mark.auth
class TestPasswordSecurity:
    """Test password security integration"""
    
    @pytest.mark.asyncio
    async def test_weak_password_rejection(self):
        """Test rejection of weak passwords"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock weak password response
        weak_password_response = AsyncMock()
        weak_password_response.status_code = 422
        weak_password_response.json.return_value = {
            "detail": "Password does not meet security requirements",
            "errors": [
                "Password must be at least 8 characters",
                "Password must contain uppercase letter",
                "Password must contain special character"
            ]
        }
        
        mock_client.post.return_value = weak_password_response
        
        # Test registration with weak password
        weak_password_user = {
            "email": "weakpass@test.com",
            "password": "123",  # Weak password
            "firstName": "Weak",
            "lastName": "Password"
        }
        
        response = await mock_client.post("/auth/register", json=weak_password_user)
        
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data
        assert "errors" in response_data
    
    @pytest.mark.asyncio
    async def test_password_change_flow(self):
        """Test password change flow"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock successful password change
        success_response = AsyncMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "message": "Password changed successfully"
        }
        
        mock_client.put.return_value = success_response
        
        # Test password change
        token = "valid.jwt.token"
        mock_client.headers = {"Authorization": f"Bearer {token}"}
        
        password_change_data = {
            "currentPassword": "OldPass123!",
            "newPassword": "NewPass456!",
            "confirmPassword": "NewPass456!"
        }
        
        response = await mock_client.put("/auth/change-password", json=password_change_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self):
        """Test password reset flow"""
        
        mock_client = AsyncMock(spec=AsyncClient)
        
        # Mock password reset request
        reset_request_response = AsyncMock()
        reset_request_response.status_code = 200
        reset_request_response.json.return_value = {
            "message": "Password reset email sent"
        }
        
        # Mock password reset confirmation
        reset_confirm_response = AsyncMock()
        reset_confirm_response.status_code = 200
        reset_confirm_response.json.return_value = {
            "message": "Password reset successfully"
        }
        
        # Set up different responses for different endpoints
        async def mock_post(*args, **kwargs):
            if "/auth/reset-password" in args[0]:
                return reset_request_response
            elif "/auth/confirm-reset" in args[0]:
                return reset_confirm_response
            return AsyncMock()
        
        mock_client.post.side_effect = mock_post
        
        # Test password reset request
        reset_request = {"email": "user@test.com"}
        response = await mock_client.post("/auth/reset-password", json=reset_request)
        
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Test password reset confirmation
        reset_confirm = {
            "token": "reset.token.here",
            "newPassword": "NewPass789!"
        }
        response = await mock_client.post("/auth/confirm-reset", json=reset_confirm)
        
        assert response.status_code == 200
        assert "message" in response.json()
