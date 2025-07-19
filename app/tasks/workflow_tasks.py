from typing import Dict, Any, List
from app.tasks.base_task import BaseTask
from app.services.notion_service import NotionService
from app.services.google_service import GoogleService

from app.auth import get_valid_google_token
import json

class NotionToGoogleTask(BaseTask):
    """
    Notion to Google Calendar workflow task.
    Fetches scheduled entries from Notion and creates Google Calendar events.
    """
    
    def __init__(self, workflow_id: int, workflow_name: str):
        super().__init__(workflow_id, workflow_name)
    
    async def execute(self, user_id: str) -> Dict[str, Any]:
        """
        Execute the Notion to Google Calendar workflow.
        """
        try:
            # Get user integrations
            integrations = await self.get_user_integrations(user_id)
            
            if "notion" not in integrations or "google" not in integrations:
                return {
                    "success": False,
                    "error": "Missing required integrations (Notion and Google)",
                    "description": "User needs both Notion and Google integrations"
                }
            
            # Get tokens
            notion_integration = integrations["notion"]
            notion_token = notion_integration["access_token"]
            
            # Get database_id from metadata
            notion_metadata = notion_integration.get("metadata", {})
            if isinstance(notion_metadata, str):
                try:
                    notion_metadata = json.loads(notion_metadata)
                except:
                    notion_metadata = {}
            
            notion_db_id = notion_metadata.get("database_id")
            if not notion_db_id:
                return {
                    "success": False,
                    "error": "No Notion database ID configured",
                    "description": "User needs to configure Notion database"
                }
            
            # Get valid Google token
            try:
                google_token = await get_valid_google_token(user_id)
            except Exception as e:
                self.log_error(user_id, "trigger", "google", f"Failed to get Google token", str(e))
                return {
                    "success": False,
                    "error": f"Failed to get Google token: {str(e)}",
                    "description": "Google authentication failed"
                }
            
            # Initialize services
            notion_service = NotionService(notion_token)
            google_service = GoogleService(google_token)
            
            # Fetch entries from Notion
            try:
                entries = await notion_service.fetch_scheduled_entries(notion_db_id)
            except Exception as e:
                self.log_error(user_id, "trigger", "notion", "Failed to fetch Notion entries", str(e))
                return {
                    "success": False,
                    "error": f"Failed to fetch Notion entries: {str(e)}",
                    "description": "Notion API error"
                }
            
            if not entries:
                return {
                    "success": True,
                    "description": "No entries to process",
                    "items_processed": 0,
                    "items_created": 0
                }
            
            # Process each entry
            meetings_scheduled = 0
            for entry in entries:
                try:
                    # Extract entry data
                    properties = entry.get("properties", {})
                    
                    title = properties.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled Meeting")
                    
                    start_date_prop = properties.get("Start Date", {})
                    start = start_date_prop.get("date", {}).get("start") if start_date_prop.get("type") == "date" else None
                    
                    end_date_prop = properties.get("End Date", {})
                    end = end_date_prop.get("date", {}).get("start") if end_date_prop.get("type") == "date" else None
                    
                    attendees_prop = properties.get("Attendees", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
                    
                    if not start or not end:
                        print(f"Skipping entry {entry.get('id')}: Missing start or end date")
                        continue
                    
                    # Process attendees
                    if attendees_prop:
                        attendees = [email.strip() for email in attendees_prop.replace('\n', ',').replace(';', ',').split(',') if email.strip()]
                    else:
                        attendees = []
                    
                    print(f"Scheduling: {title} for {attendees}")
                    
                    # Create Google Calendar event
                    event_id = await google_service.create_event(
                        summary=title,
                        start_time=start,
                        end_time=end,
                        attendees=attendees
                    )
                    
                    # Update Notion with event ID
                    if event_id:
                        success = await notion_service.update_entry_with_event_id(entry["id"], event_id)
                        if success:
                            meetings_scheduled += 1
                            print(f"✅ Scheduled meeting: {title}")
                        else:
                            self.log_error(user_id, "action", "notion", f"Failed to update Notion for meeting: {title}", "Update failed")
                    else:
                        self.log_error(user_id, "action", "google", f"Failed to create Google Calendar event for: {title}", "Event creation failed")
                        
                except Exception as e:
                    self.log_error(user_id, "action", "system", f"Failed to process meeting entry {entry.get('id')}", str(e))
                    continue
            
            return {
                "success": True,
                "description": f"Processed {len(entries)} Notion entries, scheduled {meetings_scheduled} meetings",
                "items_processed": len(entries),
                "items_created": meetings_scheduled
            }
            
        except Exception as e:
            self.log_error(user_id, "trigger", "system", "Workflow execution failed", str(e))
            return {
                "success": False,
                "error": str(e),
                "description": "Workflow execution failed"
            }

 