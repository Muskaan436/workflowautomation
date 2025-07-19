from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.celery import celery_app
import redis
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "workflow-automation",
        "version": "1.0.0"
    }

@router.get("/health/celery")
async def celery_health_check():
    """Check Celery worker status"""
    try:
        # Check if Celery can connect to broker
        i = celery_app.control.inspect()
        stats = i.stats()
        
        if stats:
            return {
                "status": "healthy",
                "celery": "connected",
                "workers": len(stats),
                "worker_stats": stats
            }
        else:
            return {
                "status": "warning",
                "celery": "connected",
                "workers": 0,
                "message": "No active workers found"
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Celery health check failed: {str(e)}")

@router.get("/health/database")
async def database_health_check():
    """Check database connection"""
    try:
        # Test database connection
        response = supabase.table("workflows").select("count", count="exact").execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "workflows_count": response.count
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")

@router.get("/health/redis")
async def redis_health_check():
    """Check Redis connection"""
    try:
        # Test Redis connection
        r = redis.from_url(settings.REDIS_CELERY_BROKER)
        r.ping()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "broker": settings.REDIS_CELERY_BROKER
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis health check failed: {str(e)}") 