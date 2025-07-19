import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from app.services.base_service import BaseService

class GoogleService(BaseService):
    """
    Google service for Calendar operations.
    """
    
    async def execute_action(self, action: str, data: Dict[str, Any]) -> Any:
        """
        Execute Google-specific actions.
        """
        if action == "create_event":
            return await self.create_event(
                summary=data.get("summary"),
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                attendees=data.get("attendees", [])
            )
        else:
            raise ValueError(f"Unknown Google action: {action}")
    
    async def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        attendees: List[str]
    ) -> Optional[str]:
        """
        Create a Google Calendar event and return the event ID with retry logic
        """
        
        # Convert ISO string to RFC3339 format for Google Calendar
        try:
            start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError as e:
            print(f"Invalid date format: {e}")
            return None
        
        event_data = {
            "summary": summary,
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "UTC"
            },
            "attendees": [{"email": email} for email in attendees if email],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 10}
                ]
            }
        }
        
        response_data = await self.make_request(
            "POST",
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            event_data
        )
        
        if response_data:
            event_id = response_data.get("id")
            print(f"Created Google Calendar event: {event_id}")
            return event_id
        else:
            print("Failed to create Google Calendar event")
            return None 