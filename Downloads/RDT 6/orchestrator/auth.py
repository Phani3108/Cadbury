"""
Authentication middleware for Digital Twin.
"""
import os
import jwt
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from msal import ConfidentialClientApplication

# Security scheme
security = HTTPBearer()

# MSAL configuration
msal_config = {
    'client_id': os.getenv('TEAMS_CLIENT_ID', ''),
    'client_secret': os.getenv('TEAMS_CLIENT_SECRET', ''),
    'authority': f"https://login.microsoftonline.com/{os.getenv('TEAMS_TENANT_ID', '')}"
}

# MSAL app instance
msal_app = None

def get_msal_app():
    """Get or create MSAL app instance."""
    global msal_app
    if msal_app is None and msal_config['client_id']:
        msal_app = ConfidentialClientApplication(
            msal_config['client_id'],
            authority=msal_config['authority'],
            client_credential=msal_config['client_secret']
        )
    return msal_app

async def verify_teams_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Teams SSO token."""
    try:
        from jwt import PyJWKClient
        
        # Production Teams JWT validation
        if os.getenv('MODE') == 'prod':
            jwks_url = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
            jwks_client = PyJWKClient(jwks_url)
            
            # Get signing key and verify
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=os.getenv("TEAMS_APP_ID"),
                issuer="https://login.microsoftonline.com/common/v2.0"
            )
        else:
            # Development: decode without verification
            decoded = jwt.decode(
                token,
                options={"verify_signature": False}
            )
        
        # Extract user info
        user_info = {
            'user_id': decoded.get('oid', 'unknown'),
            'email': decoded.get('upn', ''),
            'name': decoded.get('name', 'Unknown User'),
            'teams_id': decoded.get('tid', ''),
            'preferred_username': decoded.get('preferred_username', ''),
            'roles': decoded.get('roles', ['user'])
        }
        
        return user_info
        
    except Exception as e:
        print(f"Teams token verification failed: {e}")
        return None

async def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token."""
    try:
        # In production, verify with proper secret
        secret = os.getenv('JWT_SECRET', 'dev-secret')
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        
        user_info = {
            'user_id': decoded.get('user_id', 'unknown'),
            'email': decoded.get('email', ''),
            'name': decoded.get('name', 'Unknown User'),
            'role': decoded.get('role', 'user')
        }
        
        return user_info
        
    except Exception as e:
        print(f"JWT verification failed: {e}")
        return None

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (optional in dev mode)
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If authentication fails
    """
    # Development fallback (if no auth configured)
    if os.getenv('MODE') == 'dev' and not credentials:
        return {
            'user_id': 'dev_user',
            'email': 'dev@example.com',
            'name': 'Development User',
            'role': 'admin'
        }
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    
    token = credentials.credentials
    
    # Check if it's a Teams token (starts with 'Bearer' and contains specific claims)
    if token.startswith('Bearer '):
        token = token[7:]  # Remove 'Bearer ' prefix
    
    # Try Teams token first
    user_info = await verify_teams_token(token)
    if user_info:
        return user_info
    
    # Try JWT token
    user_info = await verify_jwt_token(token)
    if user_info:
        return user_info
    
    # Development fallback (if no auth configured)
    if os.getenv('MODE') == 'dev':
        return {
            'user_id': 'dev_user',
            'email': 'dev@example.com',
            'name': 'Development User',
            'role': 'admin'
        }
    
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token"
    )

async def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role for protected endpoints."""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user

def create_jwt_token(user_info: Dict[str, Any]) -> str:
    """Create JWT token for user."""
    secret = os.getenv('JWT_SECRET', 'dev-secret')
    payload = {
        'user_id': user_info['user_id'],
        'email': user_info['email'],
        'name': user_info['name'],
        'role': user_info.get('role', 'user'),
                    'exp': int(time.time()) + 3600  # 1 hour expiry
    }
    
    return jwt.encode(payload, secret, algorithm='HS256') 