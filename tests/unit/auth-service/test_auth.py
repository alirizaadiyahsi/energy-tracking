"""
Unit tests for authentication service
"""
import pytest
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import uuid

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
        
        # Password should be hashed
        assert hashed != password
        assert len(hashed) > 50
        
        # Should verify correctly
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_jwt_token_creation(self):
        """Test JWT token creation and validation"""
        from core.security import create_access_token, verify_token
        
        user_data = {"user_id": str(uuid.uuid4()), "email": "test@example.com"}
        token = create_access_token(user_data)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Should decode correctly
        decoded = verify_token(token)
        assert decoded["user_id"] == user_data["user_id"]
        assert decoded["email"] == user_data["email"]
    
    def test_jwt_token_expiry(self):
        """Test JWT token expiration"""
        from core.security import create_access_token, verify_token
        from jose import JWTError
        import time
        
        user_data = {"user_id": str(uuid.uuid4())}
        # Create token with 1 second expiry
        token = create_access_token(user_data, expires_delta=timedelta(seconds=1))
        
        # Should work immediately
        decoded = verify_token(token)
        assert decoded["user_id"] == user_data["user_id"]
        
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
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        mock_user.password_hash = hash_password("password123")
        mock_user.is_active = True
        
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
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        mock_user.password_hash = hash_password("password123")
        mock_user.is_active = True
        
        # Mock finding user
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
            "firstname+lastname@company.org"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "test@",
            "test.domain.com"
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


@pytest.mark.unit
@pytest.mark.auth
class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test user model creation"""
        from models.user import User
        
        user_data = {
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
        
        user = User(**user_data)
        
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == "user"
        assert user.is_active is True  # Default value
    
    def test_user_full_name(self):
        """Test user full name property"""
        from models.user import User
        
        user = User(
            email="test@example.com",
            first_name="John",
            last_name="Doe"
        )
        
        assert user.full_name == "John Doe"
    
    def test_user_permissions(self):
        """Test user permissions based on role"""
        from models.user import User
        
        admin_user = User(email="admin@example.com", role="admin")
        user_user = User(email="user@example.com", role="user")
        
        # Mock role-based permissions
        with patch('models.user.get_role_permissions') as mock_get_permissions:
            mock_get_permissions.side_effect = lambda role: {
                "admin": ["read:all", "write:all", "delete:all"],
                "user": ["read:own", "write:own"]
            }.get(role, [])
            
            admin_permissions = admin_user.get_permissions()
            user_permissions = user_user.get_permissions()
            
            assert "read:all" in admin_permissions
            assert "write:all" in admin_permissions
            assert "delete:all" in admin_permissions
            
            assert "read:own" in user_permissions
            assert "write:own" in user_permissions
            assert "delete:all" not in user_permissions


@pytest.mark.unit
@pytest.mark.auth
class TestAuthAPI:
    """Test authentication API endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_endpoint(self):
        """Test user registration endpoint"""
        from api.auth import register
        from schemas.auth import UserCreate, UserResponse
        
        # Mock dependencies
        mock_session = AsyncMock()
        mock_auth_service = AsyncMock()
        
        user_create = UserCreate(
            email="test@example.com",
            password="password123",
            firstName="Test",
            lastName="User"
        )
        
        # Mock successful user creation
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.role = "user"
        mock_user.is_active = True
        
        mock_auth_service.create_user.return_value = mock_user
        
        with patch('api.auth.get_db', return_value=mock_session), \
             patch('api.auth.AuthService', return_value=mock_auth_service):
            
            result = await register(user_create, mock_session)
            
            assert isinstance(result, UserResponse)
            assert result.email == "test@example.com"
            mock_auth_service.create_user.assert_called_once_with(user_create)
    
    @pytest.mark.asyncio
    async def test_login_endpoint(self):
        """Test user login endpoint"""
        from api.auth import login
        from schemas.auth import UserLogin, TokenResponse
        
        # Mock dependencies
        mock_session = AsyncMock()
        mock_auth_service = AsyncMock()
        
        user_login = UserLogin(
            email="test@example.com",
            password="password123"
        )
        
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        mock_user.role = "user"
        
        mock_auth_service.authenticate_user.return_value = mock_user
        
        with patch('api.auth.get_db', return_value=mock_session), \
             patch('api.auth.AuthService', return_value=mock_auth_service), \
             patch('api.auth.create_access_token', return_value="mock_token"):
            
            result = await login(user_login, mock_session)
            
            assert isinstance(result, TokenResponse)
            assert result.access_token == "mock_token"
            assert result.token_type == "bearer"
            mock_auth_service.authenticate_user.assert_called_once()


@pytest.mark.unit
@pytest.mark.auth
class TestRolePermissionSystem:
    """Test role and permission system"""
    
    def test_role_creation(self):
        """Test role model creation"""
        from models.role import Role
        
        role = Role(
            name="manager",
            description="Manager role with limited admin permissions"
        )
        
        assert role.name == "manager"
        assert role.description is not None
        assert role.is_active is True
    
    def test_permission_creation(self):
        """Test permission model creation"""
        from models.permission import Permission
        
        permission = Permission(
            name="read:devices",
            description="Read device information",
            resource="devices",
            action="read"
        )
        
        assert permission.name == "read:devices"
        assert permission.resource == "devices"
        assert permission.action == "read"
    
    def test_role_permission_assignment(self):
        """Test role-permission relationships"""
        from models.role import Role
        from models.permission import Permission
        
        role = Role(name="operator")
        permissions = [
            Permission(name="read:devices"),
            Permission(name="write:devices")
        ]
        
        # Mock relationship
        role.permissions = permissions
        
        assert len(role.permissions) == 2
        assert any(p.name == "read:devices" for p in role.permissions)
        assert any(p.name == "write:devices" for p in role.permissions)


@pytest.mark.unit
class TestSecurityUtils:
    """Test security utility functions"""
    
    def test_generate_salt(self):
        """Test salt generation"""
        from core.security import generate_salt
        
        salt1 = generate_salt()
        salt2 = generate_salt()
        
        # Salts should be different
        assert salt1 != salt2
        assert len(salt1) >= 16
        assert len(salt2) >= 16
    
    def test_token_blacklist(self):
        """Test token blacklisting functionality"""
        from core.security import add_token_to_blacklist, is_token_blacklisted
        
        token = "sample_jwt_token"
        
        # Token should not be blacklisted initially
        assert is_token_blacklisted(token) is False
        
        # Add to blacklist
        add_token_to_blacklist(token)
        
        # Token should now be blacklisted
        assert is_token_blacklisted(token) is True
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        from core.security import check_rate_limit, increment_rate_limit
        
        client_id = "test_client"
        limit = 5
        window = 60  # seconds
        
        # Should be allowed initially
        assert check_rate_limit(client_id, limit, window) is True
        
        # Increment rate limit
        for _ in range(limit):
            increment_rate_limit(client_id, window)
        
        # Should be rate limited now
        assert check_rate_limit(client_id, limit, window) is False
    
    def test_session_management(self):
        """Test session management"""
        from core.security import create_session, validate_session, invalidate_session
        
        user_id = str(uuid.uuid4())
        
        # Create session
        session_id = create_session(user_id)
        assert session_id is not None
        
        # Validate session
        assert validate_session(session_id, user_id) is True
        
        # Invalidate session
        invalidate_session(session_id)
        assert validate_session(session_id, user_id) is False
