from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

from ..schemas import SpotifyAuthRequest, SpotifyAuthResponse, SpotifyCallbackResponse
from ..services.spotify_service import SpotifyService
from ..config import settings
from ..database import get_db, User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Spotify service
spotify_service = SpotifyService(
    client_id=settings.SPOTIFY_CLIENT_ID,
    client_secret=settings.SPOTIFY_CLIENT_SECRET,
    redirect_uri=settings.SPOTIFY_REDIRECT_URI
)

@router.get("/spotify/login")
async def spotify_login():
    """
    Initiate Spotify OAuth login flow.
    Redirects user to Spotify authorization page.
    """
    try:
        auth_url = spotify_service.get_auth_url()
        logger.info("Generated Spotify OAuth URL")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Failed to generate Spotify OAuth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Spotify login")

@router.get("/callback")
async def spotify_callback(code: Optional[str] = None, state: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Handle Spotify OAuth callback.
    Exchange authorization code for access tokens and create/update user.
    """
    try:
        if not code:
            # If no code, redirect to frontend with error
            frontend_url = f"{settings.ALLOWED_ORIGINS[0]}/auth/callback?success=false&error=No authorization code provided"
            return RedirectResponse(url=frontend_url)
        
        # Exchange code for tokens
        token_info = spotify_service.get_tokens_from_code(code)
        
        if not token_info:
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
        # Get user profile from Spotify
        user_profile = spotify_service.get_user_profile(token_info['access_token'])
        logger.info(f"Spotify user profile: {user_profile}")
        
        # Check if user exists in database
        user = db.query(User).filter(User.id == user_profile['id']).first()
        
        if user:
            # Update existing user
            user.access_token = token_info['access_token']
            user.refresh_token = token_info.get('refresh_token')
            user.token_expires_at = datetime.fromisoformat(token_info['expires_at'])
            user.display_name = user_profile['display_name']
            user.email = user_profile.get('email')
            
            logger.info(f"Updated existing user: {user_profile['display_name']}")
        else:
            # Create new user
            user = User(
                id=user_profile['id'],
                display_name=user_profile['display_name'],
                email=user_profile.get('email'),
                access_token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                token_expires_at=datetime.fromisoformat(token_info['expires_at'])
            )
            db.add(user)
            logger.info(f"Created new user: {user_profile['display_name']}")
        
        # Commit changes
        db.commit()
        
        # Redirect to frontend with success
        from urllib.parse import quote
        logger.info(f"User ID for redirect: {user.id} (type: {type(user.id)})")
        frontend_url = f"{settings.ALLOWED_ORIGINS[0]}/auth/callback?success=true&user_id={quote(str(user.id))}&access_token={token_info['access_token']}"
        logger.info("Spotify authorization completed")
        return RedirectResponse(url=frontend_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Spotify callback: {str(e)}")
        # Redirect to frontend with error
        frontend_url = f"{settings.ALLOWED_ORIGINS[0]}/auth/callback?success=false&error=Authentication failed"
        return RedirectResponse(url=frontend_url)

@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """
    Refresh the access token using refresh token.
    """
    try:
        # Get user ID from request (you might want to use JWT tokens here)
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.refresh_token:
            raise HTTPException(status_code=400, detail="No refresh token available")
        
        # Check if token is expired
        if user.token_expires_at and user.token_expires_at > datetime.utcnow():
            return {
                "access_token": user.access_token,
                "expires_at": user.token_expires_at.isoformat(),
                "message": "Token is still valid"
            }
        
        # Refresh token
        token_info = spotify_service.refresh_access_token(user.refresh_token)
        
        # Update user with new token
        user.access_token = token_info['access_token']
        user.token_expires_at = datetime.fromisoformat(token_info['expires_at'])
        user.last_login = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Refreshed token for user: {user.display_name}")
        
        return {
            "access_token": token_info['access_token'],
            "expires_at": token_info['expires_at'],
            "message": "Token refreshed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")

@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """
    Logout user by invalidating their tokens.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Clear tokens
        user.access_token = None
        user.refresh_token = None
        user.token_expires_at = None
        
        db.commit()
        
        logger.info(f"User logged out: {user.display_name}")
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/status")
async def auth_status(request: Request, db: Session = Depends(get_db)):
    """
    Check authentication status and return user info if authenticated.
    """
    try:
        # Get user ID from request
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return {"authenticated": False, "message": "No user ID provided"}
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"authenticated": False, "message": "User not found"}
        
        # Check if token is expired
        if not user.access_token or (user.token_expires_at and user.token_expires_at <= datetime.utcnow()):
            return {"authenticated": False, "message": "Token expired or invalid"}
        
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "display_name": user.display_name,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return {"authenticated": False, "message": "Error checking authentication status"}

@router.get("/spotify/url")
async def get_spotify_auth_url():
    """
    Get the Spotify OAuth authorization URL without redirecting.
    Useful for frontend applications.
    """
    try:
        auth_url = spotify_service.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Failed to generate Spotify OAuth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")

