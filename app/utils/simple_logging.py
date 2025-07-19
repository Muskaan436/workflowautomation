import uuid
from datetime import datetime
from app.database import supabase

def log_execution(user_id, workflow_id, step_id, step_type, app, description, success=True, error=None):
    """
    Simple logging function for workflow executions
    
    Args:
        user_id: User identifier
        workflow_id: Workflow ID
        step_id: Step number (optional)
        step_type: 'trigger' or 'action'
        app: 'notion', 'google', etc.
        description: Human-readable description
        success: Boolean indicating success
        error: Error message if failed
    """
    try:
        supabase.table("workflow_execution_logs").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "step_type": step_type,
            "app": app,
            "description": description,
            "success": success,
            "error": error,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        print(f"✅ Logged: {description} ({'Success' if success else 'Failed'})")
        
    except Exception as e:
        print(f"❌ Failed to log execution: {str(e)}")

def log_workflow_execution(user_id, workflow_id, workflow_name, description, items_processed=0, items_created=0, success=True, error=None):
    """
    Log a complete workflow execution summary (workflow-agnostic)
    
    Args:
        user_id: User identifier
        workflow_id: Workflow ID
        workflow_name: Name of the workflow (e.g., "Notion to Google Meet")
        description: Summary description of the workflow execution
        items_processed: Number of items processed (e.g., emails, database entries)
        items_created: Number of items created (e.g., meetings, database entries)
        success: Boolean indicating success
        error: Error message if failed
    """
    try:
        supabase.table("workflow_execution_logs").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "workflow_id": workflow_id,
            "step_id": None,
            "step_type": "execution",
            "app": "workflow",
            "description": f"[{workflow_name}] {description}",
            "success": success,
            "error": error,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        print(f"✅ Workflow Execution: [{workflow_name}] {description} ({'Success' if success else 'Failed'})")
        
    except Exception as e:
        print(f"❌ Failed to log workflow execution: {str(e)}")

def log_error(user_id, workflow_id, step_type, app, description, error):
    """Log an error"""
    log_execution(user_id, workflow_id, None, step_type, app, description, False, error) 