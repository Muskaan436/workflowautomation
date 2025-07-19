from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
import asyncio

class BaseService(ABC):
    """
    Base class for all service integrations (Notion, Google, etc.)
    Provides common functionality and interface for all services.
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    @abstractmethod
    async def execute_action(self, action: str, data: Dict[str, Any]) -> Any:
        """
        Execute a specific action for this service.
        Must be implemented by each service.
        """
        raise NotImplementedError
    
    async def make_request(self, method: str, url: str, data: Optional[Dict] = None, 
                          max_retries: int = 3) -> Optional[Dict]:
        """
        Common HTTP request method with retry logic.
        """
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=self.headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=self.headers, json=data)
                    elif method.upper() == "PATCH":
                        response = await client.patch(url, headers=self.headers, json=data)
                    elif method.upper() == "PUT":
                        response = await client.put(url, headers=self.headers, json=data)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 401:
                        print(f"Authentication failed for {self.__class__.__name__}")
                        return None
                    else:
                        print(f"Request failed (attempt {attempt + 1}): {response.status_code} - {response.text}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return None
                        
            except httpx.TimeoutException:
                print(f"Timeout (attempt {attempt + 1}) for {self.__class__.__name__}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                print(f"Unexpected error (attempt {attempt + 1}) for {self.__class__.__name__}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    def validate_token(self) -> bool:
        """
        Basic token validation - can be overridden by specific services.
        """
        return bool(self.access_token and len(self.access_token) > 10) 