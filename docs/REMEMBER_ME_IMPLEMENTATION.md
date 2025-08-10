# Remember Me Functionality Implementation

## Problem
The "remember me" functionality was not working in the login flow. The frontend was sending the `remember_me` parameter, but the backend was not using it to adjust token and session expiration times.

## Root Cause
- Backend was receiving the `remember_me` parameter but ignoring it
- All sessions and tokens had fixed expiration times regardless of the remember me setting
- Frontend was storing tokens the same way regardless of remember me preference

## Solution Implemented

### Backend Changes

#### 1. Updated Authentication Service (`auth_service.py`)
- Modified `authenticate_user()` method to accept `remember_me` parameter
- Updated `_create_session()` to set different session expiration based on remember_me:
  - Normal session: 24 hours (configurable via `SESSION_EXPIRE_HOURS`)
  - Remember me session: 30 days (configurable via `SESSION_REMEMBER_ME_EXPIRE_DAYS`)
- Updated `_generate_tokens()` to create tokens with different expiration times:
  - Normal tokens: 30 minutes access, 7 days refresh (standard settings)
  - Remember me tokens: 7 days access, 30 days refresh (configurable via new settings)

#### 2. Enhanced Security Module (`security.py`)
- Added optional `expires_delta` parameter to `create_access_token()` and `create_refresh_token()` methods
- Allows custom token expiration times while maintaining backward compatibility

#### 3. Updated Session Model (`session.py`)
- Added `remember_me` Boolean column to track the preference for each session
- Enables proper token refresh behavior maintenance

#### 4. Added Configuration Settings (`config.py`)
- `JWT_REMEMBER_ME_ACCESS_TOKEN_EXPIRE_DAYS`: 7 days
- `JWT_REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS`: 30 days  
- `SESSION_REMEMBER_ME_EXPIRE_DAYS`: 30 days

#### 5. Updated API Endpoint (`auth.py`)
- Modified login endpoint to pass `remember_me` parameter to authentication service

#### 6. Database Migration
- Created `remember-me-migration.sql` to add the `remember_me` column to sessions table
- Includes index for performance and updates existing long-lived sessions

### Frontend Changes

#### 1. Enhanced AuthService (`authService.ts`)
- Added intelligent token storage strategy:
  - **Remember me**: Stores tokens in `localStorage` (persists across browser sessions)
  - **Normal login**: Stores tokens in `sessionStorage` (expires when browser closes)
- Added `rememberMe` flag in `localStorage` to track preference
- Updated all token retrieval methods to check both storage locations

#### 2. Updated API Interceptors (`authApi.ts`, `api.ts`)
- Modified to retrieve tokens from either `localStorage` or `sessionStorage`
- Maintains backward compatibility while supporting new storage strategy

#### 3. Enhanced AuthContext (`AuthContext.tsx`)
- Updated initialization to use new token storage methods
- Improved token cleanup on authentication failure

## Configuration

The remember me functionality is controlled by these environment variables:

```bash
# Standard token expiration (current defaults)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30        # 30 minutes
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7           # 7 days
SESSION_EXPIRE_HOURS=24                   # 24 hours

# Remember me token expiration (new settings)
JWT_REMEMBER_ME_ACCESS_TOKEN_EXPIRE_DAYS=7    # 7 days
JWT_REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS=30  # 30 days  
SESSION_REMEMBER_ME_EXPIRE_DAYS=30            # 30 days
```

## Security Considerations

1. **Token Storage**: Remember me tokens are stored in `localStorage` which persists across browser sessions, while normal tokens use `sessionStorage` for better security
2. **Session Tracking**: Each session stores the remember me preference, ensuring consistent behavior during token refresh
3. **Configurable Expiration**: All expiration times are configurable for different deployment environments
4. **Backward Compatibility**: Existing sessions and tokens continue to work during the transition

## Testing Results

✅ **Verification Completed**:
- Normal login: 30-minute access tokens, 24-hour sessions
- Remember me login: 7-day access tokens, 30-day sessions  
- Database correctly stores `remember_me` flag
- Frontend properly stores tokens in appropriate storage locations
- Token refresh maintains the original remember me behavior

## Files Modified

### Backend
- `services/auth-service/api/auth.py`
- `services/auth-service/services/auth_service.py`
- `services/auth-service/core/security.py`
- `services/auth-service/core/config.py`
- `services/auth-service/models/session.py`
- `scripts/remember-me-migration.sql` (new)

### Frontend  
- `frontend/src/services/authService.ts`
- `frontend/src/services/authApi.ts`
- `frontend/src/services/api.ts`
- `frontend/src/contexts/AuthContext.tsx`

## Deployment Notes

1. Run the database migration: `scripts/remember-me-migration.sql`
2. Restart the auth service to load the new model
3. Restart the frontend to load the updated code
4. Test both normal and remember me login flows

The implementation provides a secure, configurable, and user-friendly remember me functionality that enhances the user experience while maintaining security best practices.
