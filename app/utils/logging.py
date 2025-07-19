import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('celery_tasks.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('workflow_automation')

def log_task_start(task_name: str, user_id: str = None):
    """Log the start of a task"""
    logger.info(f"Starting task: {task_name}" + (f" for user: {user_id}" if user_id else ""))

def log_task_success(task_name: str, details: Dict[str, Any] = None):
    """Log successful task completion"""
    message = f"Task completed successfully: {task_name}"
    if details:
        message += f" - Details: {details}"
    logger.info(message)

def log_task_error(task_name: str, error: Exception, user_id: str = None):
    """Log task errors"""
    message = f"Task failed: {task_name}"
    if user_id:
        message += f" for user: {user_id}"
    message += f" - Error: {str(error)}"
    logger.error(message, exc_info=True)

def log_meeting_processed(title: str, event_id: str, user_id: str):
    """Log successful meeting processing"""
    logger.info(f"Meeting processed successfully - Title: {title}, Event ID: {event_id}, User: {user_id}")

def log_token_refresh(provider: str, user_id: str, success: bool):
    """Log token refresh attempts"""
    status = "successful" if success else "failed"
    logger.info(f"Token refresh {status} for {provider} - User: {user_id}") 