import os
import re
import pickle
import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from models import AIPrediction

logger = logging.getLogger(__name__)


class AIService:
    """
    Production-ready AI Service:
    - ML model prediction (if available)
    - Rule-based fallback
    - Risk intelligence layer
    - Safe DB persistence
    """

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.model_loaded = False

        self.load_model()

    # =========================
    # MODEL LOADING
    # =========================
    def load_model(self) -> bool:
        """Load trained ML model safely with fallback."""
        try:
            base_dir = os.path.dirname(__file__)
            model_path = os.path.join(
                base_dir,
                "..",
                "ml_models",
                "incident_severity_model.pkl"
            )

            if not os.path.exists(model_path):
                logger.warning("ML model not found. Switching to rule-based mode.")
                self.model_loaded = False
                return False

            with open(model_path, "rb") as f:
                model_data = pickle.load(f)

            self.model = model_data.get("model")
            self.vectorizer = model_data.get("vectorizer")
            self.label_encoder = model_data.get("label_encoder")

            if not all([self.model, self.vectorizer, self.label_encoder]):
                logger.warning("Incomplete ML model package. Using fallback.")
                self.model_loaded = False
                return False

            self.model_loaded = True
            logger.info("AI ML model loaded successfully.")
            return True

        except Exception as e:
            logger.exception(f"Model loading failed: {str(e)}")
            self.model_loaded = False
            return False

    # =========================
    # PUBLIC PREDICTION API
    # =========================
    def predict_severity(
        self,
        incident_description: str,
        db: Optional[Session] = None,
        incident_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Predict severity using ML or fallback rule-based system.
        """

        if not incident_description or not incident_description.strip():
            return {
                "predicted_severity": "LOW",
                "confidence": 0.0,
                "model_type": "invalid_input",
                "risk_factors": [],
                "suggested_mitigation": "Invalid input provided"
            }

        try:
            # ML path
            if self.model_loaded:
                return self._ml_predict(incident_description, db, incident_id)

            # fallback
            return self.rule_based_prediction(incident_description)

        except Exception as e:
            logger.exception(f"Prediction error: {str(e)}")
            return self.rule_based_prediction(incident_description)

    # =========================
    # ML PREDICTION
    # =========================
    def _ml_predict(
        self,
        text: str,
        db: Optional[Session],
        incident_id: Optional[int]
    ) -> Dict[str, Any]:

        processed = self._preprocess(text)
        vector = self.vectorizer.transform([processed])

        prediction = self.model.predict(vector)[0]
        probabilities = self.model.predict_proba(vector)[0]

        severity = self.label_encoder.inverse_transform([prediction])[0]
        confidence = float(max(probabilities))

        result = {
            "predicted_severity": severity,
            "confidence": confidence,
            "model_type": "ml",
            "model_version": "1.0.0"
        }

        if db and incident_id:
            self._save_prediction(db, incident_id, result)

        return result

    # =========================
    # RULE BASED ENGINE
    # =========================
    def rule_based_prediction(self, text: str) -> Dict[str, Any]:
        """Fallback deterministic intelligence engine."""
        text_lower = text.lower()

        critical_keywords = {
            "ransomware", "breach", "compromise", "attack",
            "unauthorized access", "data leak", "ddos",
            "malware", "encryption", "production down"
        }

        high_keywords = {
            "phishing", "suspicious", "external", "vendor",
            "security incident", "network", "violation"
        }

        medium_keywords = {
            "password", "reset", "configuration", "policy",
            "email", "minor issue"
        }

        matched_critical = [k for k in critical_keywords if k in text_lower]
        matched_high = [k for k in high_keywords if k in text_lower]
        matched_medium = [k for k in medium_keywords if k in text_lower]

        score = (len(matched_critical) * 3 +
                 len(matched_high) * 2 +
                 len(matched_medium) * 1)

        if score >= 6:
            severity = "CRITICAL"
            confidence = 0.90
        elif score >= 4:
            severity = "HIGH"
            confidence = 0.80
        elif score >= 2:
            severity = "MEDIUM"
            confidence = 0.70
        else:
            severity = "LOW"
            confidence = 0.60

        risk_factors = list(set(
            matched_critical + matched_high + matched_medium
        ))

        return {
            "predicted_severity": severity,
            "confidence": confidence,
            "risk_factors": risk_factors[:6],
            "suggested_mitigation": self._mitigation(severity),
            "model_type": "rule_based"
        }

    # =========================
    # MITIGATION ENGINE
    # =========================
    def _mitigation(self, severity: str) -> str:
        base = {
            "CRITICAL": "Immediate isolation, incident response team activation, forensic analysis, executive escalation.",
            "HIGH": "Fast investigation, containment, monitoring, preventive controls.",
            "MEDIUM": "Standard investigation, logging, corrective action.",
            "LOW": "Monitor and document."
        }
        return base.get(severity, "Monitor situation")

    # =========================
    # PREPROCESSING
    # =========================
    def _preprocess(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # =========================
    # DB PERSISTENCE
    # =========================
    def _save_prediction(
        self,
        db: Session,
        incident_id: int,
        result: Dict[str, Any]
    ):
        try:
            record = AIPrediction(
                incident_id=incident_id,
                predicted_severity=result["predicted_severity"],
                confidence_score=result["confidence"],
                model_version=result.get("model_version", "1.0"),
                risk_factors=result.get("risk_factors", []),
                suggested_mitigation=result.get("suggested_mitigation", "")
            )

            db.add(record)
            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save AI prediction: {str(e)}")

    # =========================
    # MODEL STATUS
    # =========================
    def get_model_performance(self) -> Dict[str, Any]:
        return {
            "model_loaded": self.model_loaded,
            "model_type": "ml" if self.model_loaded else "rule_based",
            "available": True
        }

    # =========================
    # RISK INTELLIGENCE LAYER
    # =========================
    def predict_emerging_risk(
        self,
        department: str,
        incident_count: int,
        avg_severity: str
    ) -> Dict[str, Any]:

        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        severity_score = severity_map.get(avg_severity, 2)

        risk_score = incident_count * severity_score

        if risk_score >= 15:
            level = "CRITICAL"
            conf = 0.95
        elif risk_score >= 10:
            level = "HIGH"
            conf = 0.85
        elif risk_score >= 5:
            level = "MEDIUM"
            conf = 0.75
        else:
            level = "LOW"
            conf = 0.60

        return {
            "department": department,
            "predicted_risk_level": level,
            "risk_score": risk_score,
            "confidence": conf,
            "recommendation": self._risk_reco(level)
        }

    def _risk_reco(self, level: str) -> str:
        return {
            "CRITICAL": "Immediate escalation + executive intervention required.",
            "HIGH": "Strengthen monitoring + allocate response team.",
            "MEDIUM": "Review controls and improve detection.",
            "LOW": "Maintain current controls."
        }.get(level, "Monitor continuously")