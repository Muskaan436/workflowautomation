import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # API Keys
    NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
    NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # App
    REDIS_CELERY_BROKER = os.getenv("REDIS_CELERY_BROKER", "redis://localhost:6379/0")
    REDIS_CELERY_BACKEND = os.getenv("REDIS_CELERY_BACKEND", "redis://localhost:6379/1")
    
    # OAuth Redirect URIs
    NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI", "http://localhost:8000/auth/notion/callback")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

settings = Settings()