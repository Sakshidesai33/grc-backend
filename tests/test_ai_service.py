"""
PRODUCTION-GRADE UNIT TESTS FOR AI SERVICE
Clean, optimized, and enterprise-level test suite

Features:
- Strict validation of AI outputs
- Deterministic behavior checks
- Edge-case coverage
- Real-world cybersecurity scenarios
- Consistent, maintainable structure
"""

import pytest
import sys
import os

# ===========================
# PATH CONFIGURATION (SAFE)
# ===========================

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ai_service import AIService


# ===========================
# SEVERITY PREDICTION TESTS
# ===========================

class TestSeverityPrediction:

    def test_critical_detection_strong_signals(self):
        cases = [
            ("Critical Security Breach", "Database fully compromised"),
            ("Ransomware Attack", "Files encrypted and locked"),
            ("System Down Emergency", "Complete infrastructure failure"),
            ("Data Breach Alert", "Sensitive data leaked externally"),
        ]

        for title, desc in cases:
            severity = AIService.predict_severity(title, desc)
            assert severity == "critical"

    def test_high_severity_detection(self):
        cases = [
            ("Phishing Campaign", "Suspicious email activity detected"),
            ("Malware Found", "Trojan detected on endpoint"),
            ("Intrusion Attempt", "Unauthorized login attempts"),
        ]

        for title, desc in cases:
            assert AIService.predict_severity(title, desc) == "high"

    def test_medium_severity_detection(self):
        cases = [
            ("Configuration Error", "Server misconfiguration detected"),
            ("Database Issue", "Connection instability observed"),
            ("Performance Degradation", "System slow response"),
        ]

        for t, d in cases:
            assert AIService.predict_severity(t, d) == "medium"

    def test_low_severity_detection(self):
        assert AIService.predict_severity(
            "Routine Update",
            "Scheduled maintenance completed"
        ) == "low"

    def test_case_insensitivity(self):
        assert AIService.predict_severity(
            "CRITICAL BREACH",
            "URGENT system failure"
        ) == "critical"


# ===========================
# INCIDENT CLASSIFICATION
# ===========================

class TestIncidentClassification:

    def test_security_categories(self):
        assert AIService.classify_incident(
            "Phishing Email",
            "Credential stealing attempt"
        ) == "Phishing"

        assert AIService.classify_incident(
            "Ransomware Detected",
            "File encryption malware"
        ) == "Malware Attack"

    def test_data_breach_classification(self):
        assert AIService.classify_incident(
            "Data Leak",
            "Customer records exposed online"
        ) == "Data Breach"

    def test_unauthorized_access(self):
        assert AIService.classify_incident(
            "Intrusion Detected",
            "Unauthorized access attempt"
        ) == "Unauthorized Access"

    def test_system_failure(self):
        assert AIService.classify_incident(
            "Server Crash",
            "Application stopped responding"
        ) == "System Failure"

    def test_ddos_detection(self):
        assert AIService.classify_incident(
            "DDoS Attack",
            "Traffic flood detected"
        ) == "DDoS Attack"

    def test_insider_threat(self):
        assert AIService.classify_incident(
            "Suspicious Employee Activity",
            "Internal misuse detected"
        ) == "Insider Threat"

    def test_general_fallback(self):
        result = AIService.classify_incident("Unknown Event", "Something happened")
        assert result in ["General Incident", "System Failure", "Security Incident"]


# ===========================
# ACTION RECOMMENDATIONS
# ===========================

class TestActionSuggestions:

    def test_phishing_actions(self):
        actions = AIService.suggest_actions("Phishing", "high")
        assert isinstance(actions, list)
        assert any("password" in a.lower() for a in actions)

    def test_malware_actions(self):
        actions = AIService.suggest_actions("Malware Attack", "critical")
        assert any("isolate" in a.lower() or "quarantine" in a.lower() for a in actions)

    def test_data_breach_actions(self):
        actions = AIService.suggest_actions("Data Breach", "critical")
        assert any("contain" in a.lower() or "notify" in a.lower() for a in actions)

    def test_unauthorized_access_actions(self):
        actions = AIService.suggest_actions("Unauthorized Access", "high")
        assert isinstance(actions, list)

    def test_system_failure_actions(self):
        actions = AIService.suggest_actions("System Failure", "medium")
        assert isinstance(actions, list)
        assert len(actions) > 0

    def test_ddos_actions(self):
        actions = AIService.suggest_actions("DDoS Attack", "critical")
        assert any("filter" in a.lower() or "mitigation" in a.lower() for a in actions)

    def test_action_format_quality(self):
        actions = AIService.suggest_actions("Phishing", "critical")

        for action in actions:
            assert isinstance(action, str)
            assert len(action.strip()) > 10
            assert action[0].isupper()  # professional formatting


# ===========================
# FULL AI PIPELINE TESTS
# ===========================

class TestAIIntegration:

    def test_full_pipeline(self):
        title = "Suspicious Phishing Attack"
        desc = "Multiple credential theft attempts detected in system"

        severity = AIService.predict_severity(title, desc)
        category = AIService.classify_incident(title, desc)
        actions = AIService.suggest_actions(category, severity)

        assert severity in ["critical", "high", "medium", "low"]
        assert isinstance(category, str)
        assert isinstance(actions, list)

    def test_multiple_real_world_scenarios(self):
        scenarios = [
            ("Ransomware Attack", "Files encrypted", "critical"),
            ("Phishing Email", "Suspicious email detected", "high"),
            ("Config Issue", "Minor misconfiguration", "medium"),
            ("System Update", "Routine maintenance", "low"),
        ]

        for title, desc, _ in scenarios:
            severity = AIService.predict_severity(title, desc)
            category = AIService.classify_incident(title, desc)
            actions = AIService.suggest_actions(category, severity)

            assert severity is not None
            assert category is not None
            assert isinstance(actions, list)

    def test_output_consistency(self):
        """Ensures deterministic behavior for same input"""

        title = "Phishing Attack"
        desc = "Email phishing attempt detected"

        results = [
            AIService.predict_severity(title, desc)
            for _ in range(3)
        ]

        assert all(r == results[0] for r in results)