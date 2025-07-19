# Celery task management with factory pattern
from datetime import datetime
from app.celery import celery_app
from app.tasks.task_factory import TaskFactory
from app.database import supabase
from app.utils.simple_logging import log_workflow_execution, log_error

@celery_app.task
def poll_notion_and_schedule_meetings():
    """
    Legacy task - now uses the new factory pattern.
    This maintains backward compatibility while using the new architecture.
    """
    import asyncio
    
    async def process_workflow():
        try:
            # Get all users with integrations
            integrations = supabase.table("user_integrations").select("*").execute().data
            print(f"Found {len(integrations)} integrations")
            
            # Group by user
            user_map = {}
            for integration in integrations:
                user_id = integration["user_id"]
                if user_id not in user_map:
                    user_map[user_id] = {}
                user_map[user_id][integration["provider"]] = integration
            
            # Process users with both Notion and Google
            users_processed = 0
            meetings_processed = 0
            
            for user_id, providers in user_map.items():
                if "notion" in providers and "google" in providers:
                    try:
                        # Create task using factory
                        task = TaskFactory.create_task("notion_to_google", 1, "Notion to Google Meet")
                        if task:
                            # Execute task
                            result = await task.run_with_logging(user_id)
                            
                            if result.get("success", False):
                                users_processed += 1
                                meetings_processed += result.get("items_created", 0)
                            else:
                                print(f"Task failed for user {user_id}: {result.get('error', 'Unknown error')}")
                        else:
                            print(f"Failed to create task for user {user_id}")
                            
                    except Exception as e:
                        print(f"Error processing user {user_id}: {str(e)}")
                        log_error(user_id, 1, "trigger", "system", f"Failed to process user {user_id}", str(e))
                        continue
            
            # Log overall summary
            log_workflow_execution(
                "system", 
                1, 
                "Notion to Google Meet",
                f"Workflow completed: {users_processed} users processed, {meetings_processed} meetings scheduled",
                users_processed,
                meetings_processed,
                True
            )
            
            print(f"✅ Workflow completed successfully. Users: {users_processed}, Meetings: {meetings_processed}")
            
        except Exception as e:
            print(f"❌ Workflow failed with error: {str(e)}")
            log_error("system", 1, "trigger", "system", "Workflow execution failed", str(e))
            raise
    
    # Run the async function
    asyncio.run(process_workflow())

@celery_app.task
def execute_workflow(workflow_type: str, user_id: str):
    """
    Generic workflow execution task using the factory pattern.
    """
    import asyncio
    
    async def run_workflow():
        try:
            # Get workflow info from database
            workflow_response = supabase.table("workflows").select("*").eq("name", workflow_type).execute()
            if not workflow_response.data:
                print(f"❌ Workflow not found: {workflow_type}")
                return
            
            workflow = workflow_response.data[0]
            
            # Create task using factory
            task = TaskFactory.create_task(workflow_type.lower().replace(" ", "_"), workflow["id"], workflow["name"])
            if task:
                # Execute task
                result = await task.run_with_logging(user_id)
                print(f"✅ Workflow {workflow_type} completed for user {user_id}: {result}")
            else:
                print(f"❌ Failed to create task for workflow: {workflow_type}")
                
        except Exception as e:
            print(f"❌ Workflow execution failed: {str(e)}")
            log_error(user_id, 1, "trigger", "system", f"Workflow execution failed: {workflow_type}", str(e))
            raise
    
    # Run the async function
    asyncio.run(run_workflow())

