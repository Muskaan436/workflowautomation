from fastapi import HTTPException, Header
from typing import Optional
from datetime import datetime, timezone, timedelta
import httpx
from app.database import supabase
from app.models.user import User
from app.config import settings

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Dependency to get current user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    
    try:
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user_response = supabase.table("users").select("*").eq("id", response.user.id).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return User(**user_response.data[0])
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

async def get_valid_google_token(user_id: str) -> str:
    """Get a valid Google access token, refreshing if necessary"""
    try:
        # Fetch current integration from Supabase
        integration_response = supabase.table("user_integrations")\
            .select("access_token, expires_at")\
            .eq("user_id", user_id)\
            .eq("provider", "google")\
            .execute()

        if not integration_response.data:
            raise ValueError("Google integration not found")

        integration = integration_response.data[0]
        access_token = integration["access_token"]
        expires_at = integration.get("expires_at")

        if expires_at:
            # Convert ISO 8601 string to aware datetime
            try:
                # Handle different datetime formats
                if expires_at.endswith('Z'):
                    expiry_time = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                else:
                    expiry_time = datetime.fromisoformat(expires_at)
                
                # Ensure expiry_time is timezone-aware
                if expiry_time.tzinfo is None:
                    expiry_time = expiry_time.replace(tzinfo=timezone.utc)
                
                if datetime.now(timezone.utc) + timedelta(minutes=5) >= expiry_time:
                    # Token is expired or about to expire
                    return await refresh_google_token(user_id)
            except (ValueError, TypeError) as e:
                # If datetime parsing fails, assume token is valid and continue
                print(f"Warning: Could not parse expiry time '{expires_at}': {e}")
                pass

        return access_token

    except Exception as e:
        raise RuntimeError(f"Failed to get valid Google token: {str(e)}")

async def refresh_google_token(user_id: str) -> str:
    """Refresh Google access token using refresh token"""
    try:
        # Get user's Google integration with refresh token
        integration_response = supabase.table("user_integrations").select("access_token, refresh_token, expires_at").eq("user_id", user_id).eq("provider", "google").execute()
        
        if not integration_response.data:
            raise Exception("Google integration not found")
        
        integration = integration_response.data[0]
        refresh_token = integration.get("refresh_token")
        
        if not refresh_token:
            raise Exception("No refresh token available")
        
        # Exchange refresh token for new access token
        token_response = httpx.post("https://oauth2.googleapis.com/token", data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        })
        
        if token_response.status_code != 200:
            raise Exception("Failed to refresh Google token")
        
        token_data = token_response.json()
        new_access_token = token_data["access_token"]
        new_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))).isoformat()
        
        # Update the database with new token
        supabase.table("user_integrations").update({
            "access_token": new_access_token,
            "expires_at": new_expires_at
        }).eq("user_id", user_id).eq("provider", "google").execute()
        
        return new_access_token
        
    except Exception as e:
        raise Exception(f"Failed to refresh Google token: {str(e)}") 