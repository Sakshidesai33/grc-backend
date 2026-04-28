from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
try:
    from app_new.services.ai_service import ai_service
except ImportError:
    ai_service = None
from app_new.core.deps import get_current_user
from app_new.models.user import User

router = APIRouter()

class IncidentAnalysisRequest(BaseModel):
    title: str
    description: str
    department: str

class SeverityResponse(BaseModel):
    severity: str
    confidence: float
    error: str

class ClassificationResponse(BaseModel):
    category: str
    confidence: float
    error: str

class AIAnalysisResponse(BaseModel):
    severity: SeverityResponse
    classification: ClassificationResponse
    recommendations: List[str]

@router.post("/analyze", response_model=AIAnalysisResponse)
def analyze_incident(
    request: IncidentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze incident using AI models"""
    
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    # Load models if not already loaded
    if not ai_service.models_loaded:
        try:
            ai_service.load_models()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to load AI models: {str(e)}")
    
    # Combine title and description for analysis
    text = f"{request.title} {request.description}"
    
    # Get predictions
    severity_result = ai_service.predict_severity(text)
    classification_result = ai_service.classify_incident(text)
    
    # Get recommendations
    recommendations = ai_service.get_recommendations(
        severity_result["severity"],
        classification_result["category"]
    )
    
    return AIAnalysisResponse(
        severity=SeverityResponse(**severity_result),
        classification=ClassificationResponse(**classification_result),
        recommendations=recommendations
    )

@router.post("/predict-severity", response_model=SeverityResponse)
def predict_severity(
    request: IncidentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Predict incident severity only"""
    
    if not ai_service.models_loaded:
        ai_service.load_models()
    
    text = f"{request.title} {request.description}"
    result = ai_service.predict_severity(text)
    
    return SeverityResponse(**result)

@router.post("/classify", response_model=ClassificationResponse)
def classify_incident(
    request: IncidentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Classify incident type only"""
    
    if not ai_service.models_loaded:
        ai_service.load_models()
    
    text = f"{request.title} {request.description}"
    result = ai_service.classify_incident(text)
    
    return ClassificationResponse(**result)

@router.post("/recommendations")
def get_recommendations(
    severity: str,
    category: str,
    current_user: User = Depends(get_current_user)
):
    """Get recommendations for given severity and category"""
    
    recommendations = ai_service.get_recommendations(severity, category)
    
    return {"recommendations": recommendations}
