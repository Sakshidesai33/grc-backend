import pytest
import asyncio
import sqlite3
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi.testclient import TestClient

# Ensure backend import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_production_ready import app, init_production_db


# =========================
# CONFIGURATION
# =========================

TEST_DB = "test_grc_production.db"


# =========================
# FIXTURES
# =========================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Ensure clean test environment before running suite.
    """
    # Cleanup old DB if exists
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Initialize DB
    init_production_db()

    yield

    # Final cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    return {
        "email": "test@example.com",
        "password": "Test@12345",
        "first_name": "Test",
        "last_name": "User",
        "role": "analyst",
        "department": "IT Security"
    }


@pytest.fixture
def sample_incident_data() -> Dict[str, Any]:
    return {
        "title": "Security Incident Alpha",
        "description": "Suspicious login detected from unknown IP",
        "severity": "high",
        "department": "IT Security",
        "category": "Security",
        "priority": "High"
    }


@pytest.fixture
def sample_compliance_data() -> Dict[str, Any]:
    return {
        "title": "Data Protection Policy",
        "description": "Ensures compliance with data protection standards",
        "category": "Security",
        "department": "IT Security"
    }


@pytest.fixture
def sample_gdpr_data() -> Dict[str, Any]:
    return {
        "request_type": "Data Access Request",
        "description": "User requesting personal data export",
        "priority": "medium",
        "requested_by": "test@example.com"
    }


# =========================
# AUTH TESTS
# =========================

class TestAuthentication:

    def test_register_user(self, client, sample_user_data):
        res = client.post("/api/auth/register", json=sample_user_data)
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == sample_user_data["email"]
        assert "id" in data

    def test_login_user(self, client, sample_user_data):
        client.post("/api/auth/register", json=sample_user_data)

        res = client.post("/api/auth/login", data={
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        })

        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_invalid_login(self, client):
        res = client.post("/api/auth/login", data={
            "username": "wrong@example.com",
            "password": "wrongpass"
        })
        assert res.status_code == 401


# =========================
# INCIDENT TESTS
# =========================

class TestIncidentModule:

    def _auth_header(self, client, user_data):
        client.post("/api/auth/register", json=user_data)
        res = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    def test_create_incident(self, client, sample_user_data, sample_incident_data):
        headers = self._auth_header(client, sample_user_data)

        res = client.post("/api/incidents", json=sample_incident_data, headers=headers)

        assert res.status_code == 200
        data = res.json()
        assert data["title"] == sample_incident_data["title"]
        assert data["status"] in ["open", "OPEN"]

    def test_update_incident(self, client, sample_user_data, sample_incident_data):
        headers = self._auth_header(client, sample_user_data)

        created = client.post("/api/incidents", json=sample_incident_data, headers=headers).json()
        incident_id = created["id"]

        update_payload = {
            "title": "Updated Incident",
            "description": "Updated description",
            "severity": "critical",
            "department": "IT Security",
            "category": "Security",
            "priority": "Critical"
        }

        res = client.put(f"/api/incidents/{incident_id}", json=update_payload, headers=headers)
        assert res.status_code == 200
        assert res.json()["title"] == "Updated Incident"

    def test_incident_assignment(self, client, sample_user_data, sample_incident_data):
        user = sample_user_data.copy()
        user["role"] = "risk_officer"
        headers = self._auth_header(client, user)

        incident = client.post("/api/incidents", json=sample_incident_data, headers=headers).json()

        res = client.post(
            f"/api/incidents/{incident['id']}/assign",
            json={"assigned_to": "assignee@test.com"},
            headers=headers
        )

        assert res.status_code == 200

    def test_incident_resolution(self, client, sample_user_data, sample_incident_data):
        user = sample_user_data.copy()
        user["role"] = "risk_officer"
        headers = self._auth_header(client, user)

        incident = client.post("/api/incidents", json=sample_incident_data, headers=headers).json()

        res = client.post(
            f"/api/incidents/{incident['id']}/resolve",
            json={
                "summary": "Resolved",
                "root_cause": "Misconfiguration",
                "actions_taken": "Fixed config"
            },
            headers=headers
        )

        assert res.status_code == 200


# =========================
# COMPLIANCE TESTS
# =========================

class TestCompliance:

    def test_create_policy(self, client, sample_user_data, sample_compliance_data):
        user = sample_user_data.copy()
        user["role"] = "compliance_officer"

        client.post("/api/auth/register", json=user)
        token = client.post("/api/auth/login", data={
            "username": user["email"],
            "password": user["password"]
        }).json()["access_token"]

        res = client.post(
            "/api/compliance-policies",
            json=sample_compliance_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert res.status_code == 200
        assert res.json()["title"] == sample_compliance_data["title"]


# =========================
# GDPR TESTS
# =========================

class TestGDPR:

    def test_create_request(self, client, sample_user_data, sample_gdpr_data):
        headers = TestIncidentModule()._auth_header(client, sample_user_data)

        res = client.post("/api/gdpr-requests", json=sample_gdpr_data, headers=headers)

        assert res.status_code == 200
        assert res.json()["request_type"] == sample_gdpr_data["request_type"]


# =========================
# AUTHORIZATION TESTS
# =========================

class TestRBAC:

    def test_admin_access(self, client, sample_user_data):
        user = sample_user_data.copy()
        user["role"] = "admin"

        headers = TestIncidentModule()._auth_header(client, user)

        assert client.get("/api/incidents", headers=headers).status_code == 200
        assert client.get("/api/audit-logs", headers=headers).status_code == 200

    def test_user_forbidden_audit(self, client, sample_user_data):
        user = sample_user_data.copy()
        user["role"] = "user"

        headers = TestIncidentModule()._auth_header(client, user)

        res = client.get("/api/audit-logs", headers=headers)
        assert res.status_code == 403


# =========================
# HEALTH CHECK
# =========================

class TestHealth:

    def test_health(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"


# =========================
# ERROR HANDLING
# =========================

class TestValidation:

    def test_invalid_incident(self, client, sample_user_data):
        headers = TestIncidentModule()._auth_header(client, sample_user_data)

        res = client.post("/api/incidents", json={
            "title": "",
            "description": "",
            "severity": "invalid",
            "department": "",
            "category": "",
            "priority": "invalid"
        }, headers=headers)

        assert res.status_code == 422


# =========================
# PERFORMANCE TEST
# =========================

class TestPerformance:

    def test_bulk_incidents(self, client, sample_user_data, sample_incident_data):
        headers = TestIncidentModule()._auth_header(client, sample_user_data)

        start = time.time()

        for i in range(8):
            payload = sample_incident_data.copy()
            payload["title"] = f"Incident {i}"
            res = client.post("/api/incidents", json=payload, headers=headers)
            assert res.status_code == 200

        duration = time.time() - start
        assert duration < 5.0


# =========================
# INTEGRATION FLOW
# =========================

class TestIntegrationFlow:

    def test_full_flow(self, client, sample_user_data, sample_incident_data):
        analyst = sample_user_data.copy()
        analyst["role"] = "analyst"
        analyst["email"] = "analyst@test.com"

        officer = sample_user_data.copy()
        officer["role"] = "risk_officer"
        officer["email"] = "officer@test.com"

        client.post("/api/auth/register", json=analyst)
        client.post("/api/auth/register", json=officer)

        analyst_token = client.post("/api/auth/login", data={
            "username": analyst["email"],
            "password": analyst["password"]
        }).json()["access_token"]

        officer_token = client.post("/api/auth/login", data={
            "username": officer["email"],
            "password": officer["password"]
        }).json()["access_token"]

        incident = client.post(
            "/api/incidents",
            json=sample_incident_data,
            headers={"Authorization": f"Bearer {analyst_token}"}
        ).json()

        incident_id = incident["id"]

        client.post(
            f"/api/incidents/{incident_id}/assign",
            json={"assigned_to": officer["email"]},
            headers={"Authorization": f"Bearer {officer_token}"}
        )

        res = client.post(
            f"/api/incidents/{incident_id}/resolve",
            json={
                "summary": "done",
                "root_cause": "test",
                "actions_taken": "fixed"
            },
            headers={"Authorization": f"Bearer {officer_token}"}
        )

        assert res.status_code == 200


# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])