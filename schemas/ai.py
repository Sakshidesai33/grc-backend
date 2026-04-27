from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


# =========================
# REQUEST SCHEMAS
# =========================

class AIPredictionRequest(BaseModel):
    """
    Request schema for AI-based incident severity prediction.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    incident_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed incident description for ML prediction"
    )

    incident_id: Optional[int] = Field(
        None,
        description="Optional incident ID for persistence"
    )

    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional incident title"
    )


class TextAnalysisRequest(BaseModel):
    """
    Request schema for NLP-based text analysis.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text content to analyze"
    )


# =========================
# RESPONSE SCHEMAS
# =========================

class AIPredictionResponse(BaseModel):
    """
    Response schema for AI severity prediction.
    """
    predicted_severity: str = Field(
        ...,
        description="Predicted severity level (LOW, MEDIUM, HIGH, CRITICAL)"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score (0–1)"
    )

    risk_factors: List[str] = Field(
        default_factory=list,
        description="Detected risk indicators in text"
    )

    suggested_mitigation: Optional[str] = Field(
        None,
        description="AI-generated mitigation suggestions"
    )

    model_type: str = Field(
        ...,
        description="Type of model used (ML / RULE_BASED / HYBRID)"
    )

    model_version: Optional[str] = Field(
        None,
        description="Version of AI model used"
    )


class TextAnalysisResponse(BaseModel):
    """
    NLP analysis response for incident text.
    """
    word_count: int
    char_count: int
    sentence_count: int

    urgency_indicators: List[str] = Field(default_factory=list)
    security_keywords: List[str] = Field(default_factory=list)

    action_required: bool = Field(
        ...,
        description="Whether immediate action is required based on analysis"
    )


class ModelPerformanceResponse(BaseModel):
    """
    AI model health and performance metrics.
    """
    model_loaded: bool
    model_type: str
    available: bool

    accuracy: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0
    )

    precision: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0
    )

    recall: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0
    )

    f1_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0
    )

    version: Optional[str] = None


# =========================
# INTERNAL / ENHANCED SCHEMAS
# =========================

class AIPredictionMeta(BaseModel):
    """
    Internal metadata for AI predictions (for DB logging).
    """
    processing_time_ms: Optional[int] = None
    model_latency_ms: Optional[int] = None
    feature_count: Optional[int] = None


class BatchAIPredictionRequest(BaseModel):
    """
    Future-ready batch prediction support.
    """
    incidents: List[AIPredictionRequest] = Field(
        ...,
        min_length=1,
        max_length=100
    )


class BatchAIPredictionResponse(BaseModel):
    """
    Batch prediction output for scalable AI pipelines.
    """
    results: List[AIPredictionResponse]
    total_processed: int
    failed_count: int = 0