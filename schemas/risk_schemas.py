from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RiskBase(BaseModel):
    title: str
    description: str
    probability: int
    impact: int
    department: Optional[str] = None
    status: str = "ACTIVE"

class RiskCreate(RiskBase):
    pass

class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    probability: Optional[int] = None
    impact: Optional[int] = None
    department: Optional[str] = None
    status: Optional[str] = None

class Risk(RiskBase):
    id: str
    risk_score: int
    risk_level: str
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
