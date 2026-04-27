import pickle
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

class AIService:
    def __init__(self):
        self.severity_model = None
        self.classification_model = None
        self.vectorizer = None
        self.models_loaded = False
        
    def load_models(self):
        """Load pre-trained ML models"""
        try:
            # Paths to your trained models
            model_dir = Path(__file__).parent.parent.parent / "ml_models"
            
            # Load severity prediction model
            severity_path = model_dir / "optimized_severity_model.pkl"
            if severity_path.exists():
                with open(severity_path, 'rb') as f:
                    self.severity_model = pickle.load(f)
            
            # Load classification model
            classification_path = model_dir / "optimized_category_model.pkl"
            if classification_path.exists():
                with open(classification_path, 'rb') as f:
                    self.classification_model = pickle.load(f)
            
            # Load vectorizer
            vectorizer_path = model_dir / "optimized_severity_vectorizer.pkl"
            if vectorizer_path.exists():
                with open(vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
            
            self.models_loaded = True
            print("✅ AI models loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to load AI models: {e}")
            self.models_loaded = False
    
    def predict_severity(self, text: str) -> Dict:
        """Predict incident severity"""
        if not self.models_loaded or not self.severity_model:
            return {"severity": "medium", "confidence": 0.5, "error": "Models not loaded"}
        
        try:
            # Vectorize input text
            if self.vectorizer:
                text_vector = self.vectorizer.transform([text])
                prediction = self.severity_model.predict(text_vector)[0]
                confidence = max(self.severity_model.predict_proba(text_vector)[0])
                
                severity_map = {0: "low", 1: "medium", 2: "high", 3: "critical"}
                return {
                    "severity": severity_map.get(prediction, "medium"),
                    "confidence": float(confidence),
                    "error": None
                }
        except Exception as e:
            return {"severity": "medium", "confidence": 0.5, "error": str(e)}
    
    def classify_incident(self, text: str) -> Dict:
        """Classify incident type"""
        if not self.models_loaded or not self.classification_model:
            return {"category": "general", "confidence": 0.5, "error": "Models not loaded"}
        
        try:
            # Use classification model (simplified for demo)
            categories = ["security", "network", "data", "system", "general"]
            # Simple keyword-based classification as fallback
            text_lower = text.lower()
            
            if "security" in text_lower or "breach" in text_lower:
                category = "security"
            elif "network" in text_lower or "connection" in text_lower:
                category = "network"
            elif "data" in text_lower or "database" in text_lower:
                category = "data"
            elif "system" in text_lower or "server" in text_lower:
                category = "system"
            else:
                category = "general"
            
            return {
                "category": category,
                "confidence": 0.8,
                "error": None
            }
        except Exception as e:
            return {"category": "general", "confidence": 0.5, "error": str(e)}
    
    def get_recommendations(self, severity: str, category: str) -> List[str]:
        """Get AI recommendations based on severity and category"""
        recommendations = {
            "critical": {
                "security": [
                    "Immediate incident response team activation",
                    "Isolate affected systems",
                    "Notify management and legal teams",
                    "Document all actions taken"
                ],
                "network": [
                    "Check network logs for suspicious activity",
                    "Implement temporary access restrictions",
                    "Verify firewall configurations",
                    "Monitor for further anomalies"
                ]
            },
            "high": {
                "security": [
                    "Security team assessment within 1 hour",
                    "Review access logs",
                    "Update security protocols"
                ],
                "network": [
                    "Network performance analysis",
                    "Check for configuration issues",
                    "Monitor system resources"
                ]
            }
        }
        
        # Default recommendations
        default_recs = [
            "Document the incident",
            "Monitor system status",
            "Review response procedures"
        ]
        
        return recommendations.get(severity, {}).get(category, default_recs)

# Global AI service instance
ai_service = AIService()
