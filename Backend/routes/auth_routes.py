"""
Authentication routes for user signup, signin, and signout.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, EmailStr
from database.supabase_client import get_supabase_client
from Backend.core.utils import logger

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str


@router.post("/signup", response_model=AuthResponse, summary="Sign Up")
async def sign_up(request: SignUpRequest):
    """
    Create a new user account.
    Returns access token and user info.
    """
    try:
        logger.info(f"AuthRoutes: Sign up attempt for {request.email}")
        supabase = get_supabase_client()

        response = supabase.auth.sign_up(
            {"email": request.email, "password": request.password}
        )

        if not response.user:
            raise HTTPException(status_code=400, detail="Sign up failed")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id,
            "email": response.user.email,
        }

    except Exception as e:
        logger.error(f"AuthRoutes: Sign up error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin", response_model=AuthResponse, summary="Sign In")
async def sign_in(request: SignInRequest):
    """
    Sign in with email and password.
    Returns access token and user info.
    """
    try:
        logger.info(f"AuthRoutes: Sign in attempt for {request.email}")
        supabase = get_supabase_client()

        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )

        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id,
            "email": response.user.email,
        }

    except Exception as e:
        logger.error(f"AuthRoutes: Sign in error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/signout", summary="Sign Out")
async def sign_out():
    """
    Sign out current user.
    """
    try:
        logger.info("AuthRoutes: Sign out")
        supabase = get_supabase_client()
        supabase.auth.sign_out()

        return {"status": "success", "message": "Signed out successfully"}

    except Exception as e:
        logger.error(f"AuthRoutes: Sign out error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", summary="Get Current User")
async def get_current_user_info():
    """
    Get current authenticated user info.
    Requires Authorization: Bearer <token> header.
    """
    try:
        supabase = get_supabase_client()
        user = supabase.auth.get_user()

        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        return {
            "user_id": user.user.id,
            "email": user.user.email,
            "created_at": user.user.created_at,
        }

    except Exception as e:
        logger.error(f"AuthRoutes: Get user error: {str(e)}")
        raise HTTPException(status_code=401, detail="Not authenticated")
