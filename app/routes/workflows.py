from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.models.user import User
from app.database import supabase
from app.auth import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/list", response_model=List[Dict[str, Any]])
async def get_all_workflows():
    """Get all workflows from database"""
    try:
        workflows_response = supabase.table("workflows").select("*").order("id").execute()
        return workflows_response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")

@router.post("/activate/{workflow_id}")
async def activate_workflow(workflow_id: int, current_user: User = Depends(get_current_user)):
    """Activate a workflow for the current user"""
    try:
        # Check if workflow exists
        workflow_response = supabase.table("workflows").select("*").eq("id", workflow_id).execute()
        if not workflow_response.data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Check if user already has this workflow activated
        existing_response = supabase.table("user_workflows").select("*").eq("user_id", str(current_user.id)).eq("workflow_id", workflow_id).execute()
        
        if existing_response.data:
            # Update existing record to active
            supabase.table("user_workflows").update({"is_active": True}).eq("user_id", str(current_user.id)).eq("workflow_id", workflow_id).execute()
            return {"status": "success", "message": "Workflow activated successfully"}
        else:
            # Create new user workflow record
            user_workflow_data = {
                "user_id": str(current_user.id),
                "workflow_id": workflow_id,
                "is_active": True
            }
            supabase.table("user_workflows").insert(user_workflow_data).execute()
            return {"status": "success", "message": "Workflow activated successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate workflow: {str(e)}")

@router.post("/deactivate/{workflow_id}")
async def deactivate_workflow(workflow_id: int, current_user: User = Depends(get_current_user)):
    """Deactivate a workflow for the current user"""
    try:
        # Update user workflow to inactive
        result = supabase.table("user_workflows").update({"is_active": False}).eq("user_id", str(current_user.id)).eq("workflow_id", workflow_id).execute()
        
        if result.data:
            return {"status": "success", "message": "Workflow deactivated successfully"}
        else:
            raise HTTPException(status_code=404, detail="User workflow not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate workflow: {str(e)}")

@router.get("/user/active", response_model=List[Dict[str, Any]])
async def get_user_active_workflows(current_user: User = Depends(get_current_user)):
    """Get all active workflows for the current user"""
    try:
        # Get user's active workflows with workflow details
        response = supabase.table("user_workflows").select("*, workflows(*)").eq("user_id", str(current_user.id)).eq("is_active", True).execute()
        
        # Format the response
        active_workflows = []
        for item in response.data:
            if item.get("workflows"):
                active_workflows.append({
                    "user_workflow_id": item["id"],
                    "workflow_id": item["workflow_id"],
                    "workflow_name": item["workflows"]["name"],
                    "activated_at": item["created_at"],
                    "is_active": item["is_active"]
                })
        
        return active_workflows
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user workflows: {str(e)}")





@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_workflow_logs(current_user: User = Depends(get_current_user), limit: int = 50):
    """Get workflow execution logs for the current user"""
    try:
        logs_response = supabase.table("workflow_execution_logs").select("*").eq("user_id", str(current_user.id)).order("created_at", desc=True).limit(limit).execute()
        return logs_response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow logs: {str(e)}")

@router.get("/analytics", response_model=Dict[str, Any])
async def get_workflow_analytics(current_user: User = Depends(get_current_user)):
    """Get workflow analytics for the current user"""
    try:
        # Get user's logs
        logs_response = supabase.table("workflow_execution_logs").select("*").eq("user_id", str(current_user.id)).execute()
        logs = logs_response.data
        
        # Calculate overall analytics
        total_actions = len(logs)
        successful_actions = len([log for log in logs if log.get("success", False)])
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
        
        # Get workflow-specific analytics
        workflow_analytics = {}
        for log in logs:
            if log.get("step_type") == "execution" and log.get("app") == "workflow":
                workflow_id = log.get("workflow_id")
                if workflow_id not in workflow_analytics:
                    workflow_analytics[workflow_id] = {
                        "executions": 0,
                        "successful": 0,
                        "failed": 0,
                        "last_execution": None
                    }
                
                workflow_analytics[workflow_id]["executions"] += 1
                if log.get("success"):
                    workflow_analytics[workflow_id]["successful"] += 1
                else:
                    workflow_analytics[workflow_id]["failed"] += 1
                
                # Track last execution
                if not workflow_analytics[workflow_id]["last_execution"] or log.get("created_at") > workflow_analytics[workflow_id]["last_execution"]:
                    workflow_analytics[workflow_id]["last_execution"] = log.get("created_at")
        
        # Get recent activity (last 10 logs)
        recent_activity = logs[:10]
        
        return {
            "overall": {
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "success_rate": round(success_rate, 1)
            },
            "workflows": workflow_analytics,
            "recent_activity": recent_activity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow analytics: {str(e)}")

