import httpx
import asyncio
from typing import List, Dict, Any
from app.services.base_service import BaseService

class NotionService(BaseService):
    """
    Notion service for database operations.
    """
    
    def __init__(self, access_token: str):
        super().__init__(access_token)
        self.headers["Notion-Version"] = "2022-06-28"
    
    async def execute_action(self, action: str, data: Dict[str, Any]) -> Any:
        """
        Execute Notion-specific actions.
        """
        if action == "fetch_entries":
            return await self.fetch_scheduled_entries(data.get("database_id"))
        elif action == "update_entry":
            return await self.update_entry_with_event_id(
                data.get("entry_id"), 
                data.get("event_id")
            )

        else:
            raise ValueError(f"Unknown Notion action: {action}")
    
    async def fetch_scheduled_entries(self, database_id: str) -> List[Dict[Any, Any]]:
        """
        Fetch scheduled entries from Notion database that need to be converted to meetings
        """
        
        # Query for entries with Schedule = "Yes"
        query = {
            "filter": {
                "and": [
                    {
                        "property": "Start Date",
                        "date": {
                            "is_not_empty": True
                        }
                    },
                    {
                        "property": "Schedule",
                        "rich_text": {
                            "equals": "Yes"
                        }
                    }
                ]
            }
        }
        
        response_data = await self.make_request(
            "POST",
            f"https://api.notion.com/v1/databases/{database_id}/query",
            query
        )
        
        if response_data:
            return response_data.get("results", [])
        else:
            # Schedule property doesn't exist, query all entries with start dates
            print("Schedule property not found, querying all entries with start dates...")
            simple_query = {
                "filter": {
                    "property": "Start Date",
                    "date": {
                        "is_not_empty": True
                    }
                }
            }
            
            response_data = await self.make_request(
                "POST",
                f"https://api.notion.com/v1/databases/{database_id}/query",
                simple_query
            )
            
            if response_data:
                return response_data.get("results", [])
            else:
                print("Error fetching Notion entries")
                return []

    async def update_entry_with_event_id(self, page_id: str, event_id: str) -> bool:
        """
        Update a Notion page Schedule to mark it as processed
        """
        
        # Update the page Schedule to Done
        update_data = {
            "properties": {
                "Schedule": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "Done"
                            }
                        }
                    ]
                }
            }
        }
        
        response_data = await self.make_request(
            "PATCH",
            f"https://api.notion.com/v1/pages/{page_id}",
            update_data
        )
        
        if response_data:
            print(f"Successfully updated Notion page {page_id} with event ID {event_id}")
            return True
        else:
            print("Failed to update Notion page")
            return False

