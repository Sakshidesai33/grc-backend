from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class IncidentBase(BaseModel):
    title: str
    description: str
    severity: str
    department: str
    status: str = "open"

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None

class IncidentResponse(IncidentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
