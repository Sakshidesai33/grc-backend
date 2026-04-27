from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Literal
from datetime import datetime


# =========================
# BASE SCHEMA
# =========================

class IncidentBase(BaseModel):
    """
    Base schema for incident reporting.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=255)

    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed incident description"
    )

    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    department: Optional[str] = Field(None, max_length=100)

    location: Optional[str] = Field(None, max_length=255)

    assigned_to_id: Optional[int] = None

    incident_date: Optional[datetime] = None

    tags: List[str] = Field(default_factory=list)


    # =========================
    # VALIDATION RULES
    # =========================

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]):
        if v:
            cleaned = [tag.strip().lower() for tag in v if tag.strip()]
            return list(set(cleaned))
        return []


# =========================
# CREATE SCHEMA
# =========================

class IncidentCreate(IncidentBase):
    """
    Schema for creating incidents.
    """
    pass


# =========================
# UPDATE SCHEMA
# =========================

class IncidentUpdate(BaseModel):
    """
    Partial update schema for incidents.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(None, min_length=1, max_length=255)

    description: Optional[str] = Field(None, min_length=10, max_length=5000)

    severity: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None

    status: Optional[Literal["OPEN", "INVESTIGATING", "MITIGATED", "CLOSED"]] = None

    department: Optional[str] = Field(None, max_length=100)

    location: Optional[str] = Field(None, max_length=255)

    assigned_to_id: Optional[int] = None

    tags: Optional[List[str]] = None


    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return v
        cleaned = [tag.strip().lower() for tag in v if tag.strip()]
        return list(set(cleaned))


# =========================
# RESPONSE SCHEMA
# =========================

class Incident(BaseModel):
    """
    Full incident response schema.
    """
    id: int
    uuid: str

    title: str
    description: str

    severity: str
    status: str

    department: Optional[str]
    location: Optional[str]

    reported_by_id: int
    assigned_to_id: Optional[int]

    incident_date: Optional[datetime]

    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)


# =========================
# COMMENT SCHEMA
# =========================

class IncidentComment(BaseModel):
    """
    Incident comment schema (internal/external notes).
    """
    comment: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = False


    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str):
        if not v.strip():
            raise ValueError("Comment cannot be empty")
        return v