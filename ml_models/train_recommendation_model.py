"""
Production-ready Incident Recommendation Model
------------------------------------------------
Improvements:
- Fixed bugs (e.g., isEmpty -> proper Python check)
- Added logging instead of print
- Optimized preprocessing (cached stopwords)
- Safer NLTK handling
- Clean sklearn pipeline structure
- Better error handling & validation
- Pathlib-based file management
- Type hints for maintainability
- More robust rule-based fallback engine
"""

from __future__ import annotations

import os
import re
import json
import pickle
import logging
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


# ----------------------------
# Logging Configuration
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("RecommendationModel")


# ----------------------------
# Safe NLTK Setup
# ----------------------------
def safe_nltk_setup() -> None:
    """Download required NLTK resources safely."""
    resources = ["stopwords", "punkt", "wordnet"]
    for res in resources:
        try:
            nltk.data.find(res)
        except LookupError:
            try:
                nltk.download(res, quiet=True)
            except Exception as e:
                logger.warning(f"NLTK download failed for {res}: {e}")


safe_nltk_setup()


# ----------------------------
# Configuration
# ----------------------------
@dataclass
class ModelConfig:
    max_features: int = 1000
    ngram_range: Tuple[int, int] = (1, 2)
    min_df: int = 1
    max_df: float = 0.95
    test_size: float = 0.2
    random_state: int = 42
    alpha: float = 0.1
    model_dir: Path = Path("ml_models")
    model_name: str = "recommendation_model.pkl"
    metadata_name: str = "recommendation_metadata.json"


# ----------------------------
# Core Model Class
# ----------------------------
class RecommendationModel:
    def __init__(self, config: ModelConfig = ModelConfig()):
        self.config = config

        self.vectorizer = TfidfVectorizer(
            max_features=config.max_features,
            stop_words="english",
            ngram_range=config.ngram_range,
            min_df=config.min_df,
            max_df=config.max_df
        )

        self.model: Optional[MultinomialNB] = None
        self.lemmatizer = WordNetLemmatizer()

        # Cache stopwords (performance improvement)
        self._stop_words = set(stopwords.words("english"))

        self.action_categories: List[str] = []
        self.model_metadata: Dict[str, Any] = {}

        self.config.model_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------
    # Text Preprocessing
    # ----------------------------
    def preprocess_text(self, text: Any) -> str:
        if not isinstance(text, str):
            text = str(text or "")

        text = text.lower()
        text = re.sub(r"[^a-zA-Z\s]", " ", text)

        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()

        cleaned_tokens = []
        for token in tokens:
            if token not in self._stop_words and len(token) > 2:
                cleaned_tokens.append(self.lemmatizer.lemmatize(token))

        return " ".join(cleaned_tokens)

    # ----------------------------
    # Synthetic Training Data
    # ----------------------------
    def generate_training_data(self) -> pd.DataFrame:
        data = [
            ("Malware detected in workstation", "Run antivirus scan", "Security"),
            ("Ransomware attack on server", "Isolate infected system", "Security"),
            ("Trojan found in email", "Update antivirus definitions", "Security"),

            ("Unauthorized login detected", "Reset credentials", "Access Control"),
            ("Account compromised", "Enable MFA", "Access Control"),

            ("Database crash during peak load", "Check hardware status", "Infrastructure"),
            ("Network failure reported", "Review network configuration", "Infrastructure"),

            ("Employee deleted production data", "Restore from backup", "Process"),

            ("Customer data exposed", "Notify compliance team", "Compliance"),

            ("Firewall policy violation detected", "Review access policies", "Policy"),

            ("Unpatched vulnerability found", "Apply security patch", "Vulnerability"),
        ]

        return pd.DataFrame(data, columns=["description", "action", "category"])

    # ----------------------------
    # Training
    # ----------------------------
    def train(self, dataset_path: Optional[str] = None) -> float:
        try:
            if dataset_path and os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                logger.info(f"Loaded dataset from {dataset_path}")
            else:
                df = self.generate_training_data()
                logger.info("Using synthetic dataset")

            if df.empty:
                raise ValueError("Dataset is empty")

            logger.info(f"Training samples: {len(df)}")

            df["processed_description"] = df["description"].apply(self.preprocess_text)

            X = self.vectorizer.fit_transform(df["processed_description"])
            y = df["action"]

            self.action_categories = sorted(df["category"].unique().tolist())

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=self.config.test_size,
                random_state=self.config.random_state,
                stratify=y if len(y.unique()) > 1 else None
            )

            self.model = MultinomialNB(alpha=self.config.alpha)
            self.model.fit(X_train, y_train)

            predictions = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, predictions)

            logger.info(f"Model Accuracy: {accuracy:.4f}")
            logger.info("\n" + classification_report(y_test, predictions))

            self.model_metadata = {
                "accuracy": float(accuracy),
                "trained_at": datetime.utcnow().isoformat(),
                "model": "MultinomialNB",
                "features": self.config.max_features,
            }

            self.save_model()

            return accuracy

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    # ----------------------------
    # Persistence
    # ----------------------------
    def save_model(self) -> None:
        if not self.model:
            raise ValueError("Model not trained")

        model_path = self.config.model_dir / self.config.model_name
        metadata_path = self.config.model_dir / self.config.metadata_name

        payload = {
            "vectorizer": self.vectorizer,
            "model": self.model,
            "action_categories": self.action_categories,
            "metadata": self.model_metadata,
        }

        with open(model_path, "wb") as f:
            pickle.dump(payload, f)

        metadata = {
            **self.model_metadata,
            "action_categories": self.action_categories,
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved at {model_path}")

    def load_model(self, path: Optional[str] = None) -> bool:
        try:
            model_path = Path(path) if path else self.config.model_dir / self.config.model_name

            with open(model_path, "rb") as f:
                data = pickle.load(f)

            self.vectorizer = data["vectorizer"]
            self.model = data["model"]
            self.action_categories = data["action_categories"]
            self.model_metadata = data.get("metadata", {})

            logger.info("Model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    # ----------------------------
    # ML-Based Recommendation
    # ----------------------------
    def recommend_actions(self, incident_description: str, top_k: int = 5) -> Dict[str, Any]:
        if not self.model:
            raise ValueError("Model not loaded")

        processed = self.preprocess_text(incident_description)
        vector = self.vectorizer.transform([processed])

        probs = self.model.predict_proba(vector)[0]
        classes = self.model.classes_

        ranked = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)

        return {
            "recommended_actions": [
                {
                    "action": action,
                    "confidence": float(score),
                    "priority": (
                        "HIGH" if score > 0.5 else
                        "MEDIUM" if score > 0.3 else
                        "LOW"
                    )
                }
                for action, score in ranked[:top_k]
            ],
            "model_type": "ml_based",
            "total_actions_considered": len(classes),
        }

    # ----------------------------
    # Rule-Based Fallback
    # ----------------------------
    def recommend_actions_rule_based(self, incident_description: str) -> Dict[str, Any]:
        text = (incident_description or "").lower()
        recommendations: List[Dict[str, Any]] = []

        def add(action, conf, priority):
            recommendations.append({
                "action": action,
                "confidence": conf,
                "priority": priority
            })

        if any(k in text for k in ["malware", "virus", "ransomware", "trojan"]):
            add("Run antivirus scan", 0.9, "HIGH")
            add("Isolate infected systems", 0.85, "HIGH")

        elif any(k in text for k in ["unauthorized", "compromised", "access"]):
            add("Reset credentials", 0.9, "HIGH")
            add("Enable MFA", 0.85, "HIGH")

        elif any(k in text for k in ["crash", "failure", "down", "outage"]):
            add("Check system logs", 0.85, "HIGH")
            add("Activate failover", 0.8, "HIGH")

        elif any(k in text for k in ["data", "breach", "leak"]):
            add("Notify compliance team", 0.9, "HIGH")
            add("Assess exposure scope", 0.85, "HIGH")

        elif any(k in text for k in ["vulnerability", "patch", "ssl"]):
            add("Apply security patch", 0.9, "HIGH")
            add("Run vulnerability scan", 0.85, "HIGH")

        if not recommendations:
            add("Investigate incident", 0.5, "LOW")
            add("Collect logs", 0.45, "LOW")

        return {
            "recommended_actions": recommendations,
            "model_type": "rule_based",
            "total_actions_considered": len(recommendations),
        }


# ----------------------------
# CLI Training Entry
# ----------------------------
if __name__ == "__main__":
    model = RecommendationModel()
    acc = model.train()
    logger.info(f"Training complete. Accuracy: {acc:.4f}")