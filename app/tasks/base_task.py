from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.utils.simple_logging import log_workflow_execution, log_error
from app.database import supabase
import asyncio

class BaseTask(ABC):
    """
    Base class for all workflow tasks.
    Provides common functionality and logging for all tasks.
    """
    
    def __init__(self, workflow_id: int, workflow_name: str):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
    
    @abstractmethod
    async def execute(self, user_id: str) -> Dict[str, Any]:
        """
        Execute the workflow task.
        Must be implemented by each task.
        Returns: Dict with execution results
        """
        raise NotImplementedError
    
    async def get_user_integrations(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's integrations for this workflow.
        """
        try:
            integrations_response = supabase.table("user_integrations").select("*").eq("user_id", user_id).execute()
            integrations = integrations_response.data
            
            # Group by provider
            user_integrations = {}
            for integration in integrations:
                user_integrations[integration["provider"]] = integration
            
            return user_integrations
        except Exception as e:
            print(f"Failed to get integrations for user {user_id}: {str(e)}")
            return {}
    
    def log_success(self, user_id: str, description: str, items_processed: int = 0, items_created: int = 0):
        """
        Log successful workflow execution.
        """
        log_workflow_execution(
            user_id=user_id,
            workflow_id=self.workflow_id,
            workflow_name=self.workflow_name,
            description=description,
            items_processed=items_processed,
            items_created=items_created,
            success=True
        )
    
    def log_error(self, user_id: str, step_type: str, app: str, description: str, error: str):
        """
        Log workflow execution error.
        """
        log_error(
            user_id=user_id,
            workflow_id=self.workflow_id,
            step_type=step_type,
            app=app,
            description=description,
            error=error
        )
    
    def log_start(self, user_id: str):
        """
        Log workflow start.
        """
        print(f"🔄 Starting {self.workflow_name} for user {user_id}")
    
    def log_completion(self, user_id: str, results: Dict[str, Any]):
        """
        Log workflow completion.
        """
        print(f"✅ Completed {self.workflow_name} for user {user_id}")
        print(f"   Results: {results}")
    
    async def run_with_logging(self, user_id: str) -> Dict[str, Any]:
        """
        Execute task with comprehensive logging.
        """
        try:
            self.log_start(user_id)
            
            # Execute the task
            results = await self.execute(user_id)
            
            # Log success
            if results.get("success", False):
                self.log_success(
                    user_id=user_id,
                    description=results.get("description", f"Completed {self.workflow_name}"),
                    items_processed=results.get("items_processed", 0),
                    items_created=results.get("items_created", 0)
                )
            
            self.log_completion(user_id, results)
            return results
            
        except Exception as e:
            error_msg = f"Failed to execute {self.workflow_name}: {str(e)}"
            print(f"❌ {error_msg}")
            
            self.log_error(
                user_id=user_id,
                step_type="trigger",
                app="system",
                description=f"Workflow execution failed: {self.workflow_name}",
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "description": f"Failed to execute {self.workflow_name}"
            } 