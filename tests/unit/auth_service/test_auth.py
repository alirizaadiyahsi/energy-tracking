"""
Unit tests for authentication service
"""
import pytest
import sys
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add auth service to path
auth_service_path = Path(__file__).parent.parent.parent.parent / "services" / "auth-service"
sys.path.insert(0, str(auth_service_path))


@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Test authentication business logic"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        from core.security import hash_password, verify_password
        
        password = "testpassword123"
        hashed = hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        assert len(hashed) > 20
        
        # Should verify correctly
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_jwt_token_creation(self):
        """Test JWT token creation and validation"""
        from core.security import create_access_token, verify_token
        
        user_data = {"user_id": "123", "email": "test@example.com"}
        token = create_access_token(user_data)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Should decode correctly
        decoded = verify_token(token)
        assert decoded["user_id"] == "123"
        assert decoded["email"] == "test@example.com"
    
    def test_jwt_token_expiry(self):
        """Test JWT token expiration"""
        from core.security import create_access_token, verify_token
        from jose import JWTError
        import time
        
        user_data = {"user_id": "123"}
        # Create token with 1 second expiry
        token = create_access_token(user_data, expires_delta=1)
        
        # Should work immediately
        decoded = verify_token(token)
        assert decoded["user_id"] == "123"
        
        # Wait for expiration
        time.sleep(2)
        
        # Should raise error when expired
        with pytest.raises(JWTError):
            verify_token(token)
    
    @pytest.mark.asyncio
    async def test_user_creation(self):
        """Test user creation service"""
        from services.auth_service import AuthService
        from schemas.auth import UserCreate
        
        # Mock database session
        mock_session = AsyncMock()
        auth_service = AuthService(mock_session)
        
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            firstName="Test",
            lastName="User"
        )
        
        # Mock user doesn't exist
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none = Mock(return_value=None)
        
        with patch('services.auth_service.User') as mock_user_class:
            mock_user = Mock()
            mock_user_class.return_value = mock_user
            
            result = await auth_service.create_user(user_data)
            
            # Verify user was created
            mock_user_class.assert_called_once()
            mock_session.add.assert_called_once_with(mock_user)
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_login(self):
        """Test user login service"""
        from services.auth_service import AuthService
        from models.user import User
        from core.security import hash_password
        
        mock_session = AsyncMock()
        auth_service = AuthService(mock_session)
        
        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.id = "123"
        mock_user.email = "test@example.com"
        mock_user.passwordHash = hash_password("password123")
        mock_user.isActive = True
        
        # Mock finding user
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none = Mock(return_value=mock_user)
        
        result = await auth_service.authenticate_user("test@example.com", "password123")
        
        assert result is not None
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_user_login_wrong_password(self):
        """Test user login with wrong password"""
        from services.auth_service import AuthService
        from models.user import User
        from core.security import hash_password
        
        mock_session = AsyncMock()
        auth_service = AuthService(mock_session)
        
        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.passwordHash = hash_password("password123")
        mock_user.isActive = True
        
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none = Mock(return_value=mock_user)
        
        result = await auth_service.authenticate_user("test@example.com", "wrongpassword")
        
        assert result is None
    
    def test_permission_validation(self):
        """Test permission validation logic"""
        from core.security import check_permission
        
        user_permissions = ["read:devices", "write:devices", "read:users"]
        
        assert check_permission(user_permissions, "read:devices") is True
        assert check_permission(user_permissions, "write:devices") is True
        assert check_permission(user_permissions, "delete:devices") is False
        assert check_permission(user_permissions, "admin:users") is False
    
    def test_role_hierarchy(self):
        """Test role hierarchy validation"""
        from core.security import has_role_or_higher
        
        role_hierarchy = ["viewer", "operator", "manager", "admin"]
        
        assert has_role_or_higher("admin", "viewer", role_hierarchy) is True
        assert has_role_or_higher("manager", "operator", role_hierarchy) is True
        assert has_role_or_higher("operator", "admin", role_hierarchy) is False
        assert has_role_or_higher("viewer", "manager", role_hierarchy) is False


@pytest.mark.unit
class TestAuthHelpers:
    """Test authentication helper functions"""
    
    def test_email_validation(self):
        """Test email validation"""
        from core.security import validate_email
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@gmail.com"
        ]
        
        invalid_emails = [
            "notanemail",
            "@domain.com",
            "test@",
            "test@domain",
            ""
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
        
        for email in invalid_emails:
            assert validate_email(email) is False
    
    def test_password_strength(self):
        """Test password strength validation"""
        from core.security import validate_password_strength
        
        strong_passwords = [
            "StrongP@ssw0rd",
            "MyP@ssw0rd123",
            "S3cur3P@ss!"
        ]
        
        weak_passwords = [
            "password",
            "123456",
            "password123",
            "short"
        ]
        
        for password in strong_passwords:
            result = validate_password_strength(password)
            assert result["is_valid"] is True
        
        for password in weak_passwords:
            result = validate_password_strength(password)
            assert result["is_valid"] is False
            assert len(result["issues"]) > 0
