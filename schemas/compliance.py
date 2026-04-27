from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Literal
from datetime import date, datetime


# =========================
# BASE SCHEMA
# =========================

class ComplianceBase(BaseModel):
    """
    Base compliance policy schema with strict validation.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    policy_name: str = Field(..., min_length=1, max_length=255)

    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed policy description"
    )

    regulation: Optional[str] = Field(
        None,
        max_length=100,
        description="e.g., GDPR, SOX, HIPAA"
    )

    department: Optional[str] = Field(
        None,
        max_length=100
    )

    compliance_status: Literal["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"] = Field(
        default="PENDING_REVIEW"
    )

    compliance_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Compliance score percentage"
    )

    last_audit_date: Optional[date] = None

    next_audit_date: date = Field(
        ...,
        description="Next scheduled audit date"
    )

    evidence_documents: List[str] = Field(
        default_factory=list,
        description="List of evidence file paths or URLs"
    )

    assigned_auditor_id: Optional[int] = None

    audit_frequency: Literal["MONTHLY", "QUARTERLY", "ANNUAL"] = Field(
        default="ANNUAL"
    )


    # =========================
    # VALIDATION RULES
    # =========================

    @field_validator("policy_name")
    @classmethod
    def validate_policy_name(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Policy name cannot be empty")
        return v

    @field_validator("next_audit_date")
    @classmethod
    def validate_audit_date(cls, v: date):
        if v < date.today():
            raise ValueError("Next audit date cannot be in the past")
        return v


# =========================
# CREATE SCHEMA
# =========================

class ComplianceCreate(ComplianceBase):
    """
    Schema used when creating compliance policies.
    """
    pass


# =========================
# UPDATE SCHEMA
# =========================

class ComplianceUpdate(BaseModel):
    """
    Partial update schema for compliance policies.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    policy_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    regulation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)

    compliance_status: Optional[Literal["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]] = None

    compliance_score: Optional[float] = Field(None, ge=0.0, le=100.0)

    last_audit_date: Optional[date] = None
    next_audit_date: Optional[date] = None

    evidence_documents: Optional[List[str]] = None

    assigned_auditor_id: Optional[int] = None

    audit_frequency: Optional[Literal["MONTHLY", "QUARTERLY", "ANNUAL"]] = None


# =========================
# RESPONSE SCHEMA
# =========================

class Compliance(BaseModel):
    """
    Full compliance policy response schema.
    """
    id: int
    uuid: str

    policy_name: str
    description: Optional[str]

    regulation: Optional[str]
    department: Optional[str]

    compliance_status: str
    compliance_score: Optional[float]

    last_audit_date: Optional[date]
    next_audit_date: date

    evidence_documents: List[str]

    assigned_auditor_id: Optional[int]
    audit_frequency: str

    created_at: datetime
    updated_at: datetime


# =========================
# AUDIT FINDINGS
# =========================

class AuditFinding(BaseModel):
    """
    Schema for compliance audit findings.
    """
    finding: str = Field(..., min_length=1, max_length=5000)

    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        default="LOW"
    )

    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED"] = Field(
        default="OPEN"
    )

    due_date: Optional[date] = None