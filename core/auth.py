"""
JWT Bearer authentication for FastAPI with Supabase.
"""
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from config.settings import get_settings
from core.utils import logger

settings = get_settings()

class JWTBearer(HTTPBearer):
    """JWT Bearer authentication class."""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            
            payload = self.verify_jwt(credentials.credentials)
            if not payload:
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            
            # Attach user info to request state
            request.state.user_id = payload.get("sub")
            request.state.email = payload.get("email")
            
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> dict:
        """
        Verify JWT token and return payload.
        Returns None if invalid.
        """
        try:
            # Decode JWT using Supabase JWT secret
            payload = jwt.decode(
                jwtoken,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in JWT verification: {str(e)}")
            return None


def get_current_user(request: Request) -> str:
    """Get current user ID from request state (set by JWTBearer)."""
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.user_id
