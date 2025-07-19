from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
import secrets
from datetime import datetime, timezone, timedelta

from typing import Dict, List
from urllib.parse import urlencode

from app.config import settings
from app.database import supabase
from app.models.user import User, UserCreate, UserIntegration

router = APIRouter()

class AuthResponse(BaseModel):
    access_token: str
    user: User

class LoginRequest(BaseModel):
    email: str
    password: str



@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: UserCreate):
    try:
        # Check if email confirmation is required
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if response.user:
            user_record = {
                "id": response.user.id,
                "email": user_data.email,
                "name": user_data.name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Insert user into our custom users table
            supabase.table("users").insert(user_record).execute()
            
            # Check if user needs email confirmation
            if response.session:
                # User is immediately confirmed (email confirmation disabled)
                return AuthResponse(
                    access_token=response.session.access_token,
                    user=User(**user_record)
                )
            else:
                # User needs email confirmation
                raise HTTPException(
                    status_code=400, 
                    detail="Please check your email to confirm your account before logging in."
                )
        else:
            raise HTTPException(status_code=400, detail="Signup failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")

@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        if response.user:
            user_response = supabase.table("users").select("*").eq("id", response.user.id).execute()
            user_data = user_response.data[0] if user_response.data else {}
            return AuthResponse(
                access_token=response.session.access_token,
                user=User(**user_data)
            )
        raise HTTPException(status_code=400, detail="Login failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")

# OAuth Integration Endpoints
@router.get("/google/connect")
async def connect_google(user_id: str):
    """Start Google OAuth flow for Calendar"""
    query = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id
    })
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}")



@router.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    code = request.query_params.get("code")
    user_id = request.query_params.get("state")
    
    if not code or not user_id:
        raise HTTPException(status_code=400, detail="Missing authorization code or user ID")

    try:
        # Exchange code for tokens
        token_response = httpx.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        })
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=f"OAuth error: {token_data.get('error_description', 'Unknown error')}")
        
        # Save integration to database
        integration_data = {
            "user_id": user_id,
            "provider": "google",
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))).isoformat()
        }
        
        # Check if integration already exists
        existing = supabase.table("user_integrations").select("*").eq("user_id", user_id).eq("provider", "google").execute()
        
        if existing.data:
            # Update existing integration
            supabase.table("user_integrations").update(integration_data).eq("user_id", user_id).eq("provider", "google").execute()
        else:
            # Insert new integration
            supabase.table("user_integrations").insert(integration_data).execute()
        
        return {"status": "success", "message": "Google Calendar integration connected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect Google: {str(e)}")



@router.get("/notion/connect")
async def connect_notion(user_id: str, database_id: str = None):
    """Start Notion OAuth flow with optional database selection"""
    # Encode user_id and database_id in state parameter
    state_data = {"user_id": user_id}
    if database_id:
        state_data["database_id"] = database_id
    
    import json
    import base64
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    
    query = urlencode({
        "owner": "user",
        "client_id": settings.NOTION_CLIENT_ID,
        "redirect_uri": settings.NOTION_REDIRECT_URI,
        "response_type": "code",
        "state": state
    })
    return RedirectResponse(url=f"https://api.notion.com/v1/oauth/authorize?{query}")

@router.get("/notion/callback")
async def notion_callback(request: Request):
    """Handle Notion OAuth callback and capture selected database"""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code or state")

    try:
        # Decode state parameter
        import json
        import base64
        state_data = json.loads(base64.urlsafe_b64decode(state).decode())
        user_id = state_data.get("user_id")
        database_id = state_data.get("database_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Exchange code for tokens
        token_response = httpx.post(
            "https://api.notion.com/v1/oauth/token",
            auth=(settings.NOTION_CLIENT_ID, settings.NOTION_CLIENT_SECRET),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.NOTION_REDIRECT_URI
            }
        )
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=f"OAuth error: {token_data.get('error_description', 'Unknown error')}")
        
        # Prepare metadata with database_id if provided
        metadata = {}
        if database_id:
            metadata["database_id"] = database_id
        
        # Save integration to database with metadata
        integration_data = {
            "user_id": user_id,
            "provider": "notion",
            "access_token": token_data["access_token"],
            "refresh_token": None,  # Notion doesn't provide refresh tokens
            "expires_at": None,  # Notion tokens don't expire
            "metadata": metadata
        }
        
        # Check if integration already exists
        existing = supabase.table("user_integrations").select("*").eq("user_id", user_id).eq("provider", "notion").execute()
        
        if existing.data:
            # Update existing integration
            supabase.table("user_integrations").update(integration_data).eq("user_id", user_id).eq("provider", "notion").execute()
        else:
            # Insert new integration
            supabase.table("user_integrations").insert(integration_data).execute()
        
        message = "Notion integration connected successfully"
        if database_id:
            message += f" with database ID: {database_id}"
        
        return {"status": "success", "message": message, "database_id": database_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect Notion: {str(e)}")

# Enhanced database selection endpoint

@router.get("/integrations")
async def get_user_integrations(user_id: str):
    """Get all integrations for a user"""
    try:
        response = supabase.table("user_integrations").select("*").eq("user_id", user_id).execute()
        
        if response.data:
            # Remove sensitive data before returning
            integrations = []
            for integration in response.data:
                safe_integration = {
                    "id": integration["id"],
                    "provider": integration["provider"],
                    "created_at": integration["created_at"],
                    "metadata": integration.get("metadata", {})
                }
                integrations.append(safe_integration)
            
            return {"status": "success", "integrations": integrations}
        else:
            return {"status": "success", "integrations": []}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integrations: {str(e)}")

