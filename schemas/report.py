from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportBase(BaseModel):
    title: str
    content: str
    report_type: str

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int
    generated_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True
