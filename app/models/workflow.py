from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class AppType(str, Enum):
    NOTION = "notion"
    GOOGLE = "google"

    SLACK = "slack"

class StepType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"

class Workflow(BaseModel):
    id: int
    name: str
    created_at: datetime

class Step(BaseModel):
    id: int
    workflow_id: int
    index: int
    type: StepType
    app: AppType
    step_metadata: Dict[str, Any]
    created_at: datetime

class UserWorkflow(BaseModel):
    id: int
    user_id: str
    workflow_id: int
    is_active: bool
    created_at: datetime