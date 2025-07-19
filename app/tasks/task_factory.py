from typing import Dict, Type, Optional
from app.tasks.base_task import BaseTask
from app.tasks.workflow_tasks import NotionToGoogleTask

class TaskFactory:
    """
    Factory for creating workflow tasks.
    Makes it easy to add new workflows without modifying existing code.
    """
    
    _tasks: Dict[str, Type[BaseTask]] = {}
    
    @classmethod
    def register_task(cls, task_type: str, task_class: Type[BaseTask]):
        """
        Register a new task type.
        """
        cls._tasks[task_type] = task_class
    
    @classmethod
    def create_task(cls, task_type: str, workflow_id: int, workflow_name: str) -> Optional[BaseTask]:
        """
        Create a task instance by type.
        """
        if task_type not in cls._tasks:
            return None
        
        task_class = cls._tasks[task_type]
        return task_class(workflow_id, workflow_name)
    
    @classmethod
    def get_available_tasks(cls) -> Dict[str, str]:
        """
        Get all available task types and their descriptions.
        """
        return {
            task_type: task_class.__doc__ or f"{task_class.__name__} workflow"
            for task_type, task_class in cls._tasks.items()
        }
    
    @classmethod
    def list_tasks(cls):
        """
        List all registered tasks.
        """
        print("📋 Available Workflow Tasks:")
        for task_type, task_class in cls._tasks.items():
            print(f"  • {task_type}: {task_class.__name__}")
        return list(cls._tasks.keys())

# Register default tasks
TaskFactory.register_task("notion_to_google", NotionToGoogleTask) 