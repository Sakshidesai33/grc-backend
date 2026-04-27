"""
Production-Grade CRUD Test Suite (10/10 Upgrade)
================================================

Upgrades applied:
- Clean test isolation strategy
- Strong typing + predictable assertions
- Reduced redundancy + improved structure
- Real-world validation logic checks
- Safer DB dependency handling
- Scalable test patterns for enterprise backend
- Improved failure readability
"""

import pytest
import sys
import os
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------
# PATH SETUP (ROBUST IMPORT HANDLING)
# ---------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import crud
import schemas as schemas_module
import models as models_module


# ============================================================
# USER CRUD TESTS
# ============================================================

class TestUserCRUD:
    """Production-level tests for User CRUD operations"""

    def test_create_user(self, db: Session):
        """Validate user creation with role-based integrity"""

        user_data = schemas_module.UserCreate(
            name="Alice Manager",
            email="alice@example.com",
            password="SecurePass@123",
            role="risk_manager"
        )

        user = crud.create_user(db, user_data)

        assert user is not None
        assert user.id is not None
        assert user.email == user_data.email
        assert user.name == user_data.name
        assert user.role == "risk_manager"
        assert user.is_active is True

    def test_get_user_by_id(self, db: Session, test_user):
        """Validate retrieval of user by ID"""

        user = crud.get_user(db, test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_user_by_email(self, db: Session, test_user):
        """Validate retrieval of user by email"""

        user = crud.get_user_by_email(db, test_user.email)

        assert user is not None
        assert user.email == test_user.email

    def test_get_user_not_found(self, db: Session):
        """Ensure missing user returns None safely"""

        user = crud.get_user(db, 999999)
        assert user is None

    def test_get_users_list(self, db: Session, test_user):
        """Validate user listing with pagination support"""

        extra_user = schemas_module.UserCreate(
            name="Bob Analyst",
            email="bob@example.com",
            password="SecurePass@123",
            role="analyst"
        )

        crud.create_user(db, extra_user)

        users = crud.get_users(db, skip=0, limit=50)

        assert isinstance(users, list)
        assert len(users) >= 2

    def test_authentication_success(self, db: Session):
        """Validate correct authentication flow"""

        user_data = schemas_module.UserCreate(
            name="Charlie Officer",
            email="charlie@example.com",
            password="TestPass123",
            role="compliance_officer"
        )

        crud.create_user(db, user_data)

        auth_user = crud.authenticate_user(
            db,
            "charlie@example.com",
            "TestPass123"
        )

        assert auth_user is not False
        assert auth_user.email == user_data.email

    def test_authentication_failure_wrong_password(self, db: Session):
        """Ensure invalid password fails authentication"""

        user_data = schemas_module.UserCreate(
            name="Diana",
            email="diana@example.com",
            password="CorrectPass123",
            role="employee"
        )

        crud.create_user(db, user_data)

        result = crud.authenticate_user(
            db,
            "diana@example.com",
            "WrongPassword"
        )

        assert result is False

    def test_authentication_failure_missing_user(self, db: Session):
        """Ensure missing user authentication fails safely"""

        result = crud.authenticate_user(
            db,
            "missing@example.com",
            "anyPassword"
        )

        assert result is False


# ============================================================
# INCIDENT CRUD TESTS
# ============================================================

class TestIncidentCRUD:
    """Production-grade Incident CRUD validation"""

    def test_create_incident(self, db: Session, test_user):
        """Validate incident creation lifecycle"""

        incident_data = schemas_module.IncidentCreate(
            title="Phishing Campaign Detected",
            description="Multiple phishing emails targeting finance team",
            severity="critical",
            department="Finance",
            assigned_team="Security Response",
            reported_by="System",
            category="Phishing"
        )

        incident = crud.create_incident(db, incident_data)

        assert incident.id is not None
        assert incident.title == incident_data.title
        assert incident.severity == "critical"
        assert incident.status == "open"
        assert isinstance(incident.timeline, (list, str, type(None)))

    def test_get_incident_by_id(self, db: Session, test_incident):
        """Validate incident retrieval"""

        incident = crud.get_incident(db, test_incident.id)

        assert incident is not None
        assert incident.id == test_incident.id

    def test_incident_listing(self, db: Session, test_incident):
        """Validate incident list retrieval"""

        incidents = crud.get_incidents(db, skip=0, limit=100)

        assert isinstance(incidents, list)
        assert len(incidents) >= 1

    def test_department_filtering(self, db: Session, test_incident):
        """Validate department-based filtering"""

        incidents = crud.get_incidents_by_department(db, "IT Security")

        assert isinstance(incidents, list)
        assert all(i.department == "IT Security" for i in incidents)

    def test_incident_update(self, db: Session, test_incident):
        """Validate incident update logic"""

        update_data = schemas_module.IncidentUpdate(
            status="mitigated",
            description="Updated incident details"
        )

        updated = crud.update_incident(db, test_incident.id, update_data)

        assert updated is not None
        assert updated.status == "mitigated"

    def test_incident_delete(self, db: Session, test_incident):
        """Validate safe deletion of incident"""

        crud.delete_incident(db, test_incident.id)

        deleted = crud.get_incident(db, test_incident.id)
        assert deleted is None


# ============================================================
# RISK CRUD TESTS
# ============================================================

class TestRiskCRUD:
    """Production-grade Risk management tests"""

    def test_create_risk(self, db: Session):
        """Validate risk creation and scoring"""

        risk_data = schemas_module.RiskCreate(
            risk_title="Insider Threat",
            probability=4,
            impact=5,
            department="HR"
        )

        risk = crud.create_risk(db, risk_data)

        assert risk.id is not None
        assert risk.risk_title == "Insider Threat"
        assert risk.risk_score == risk.probability * risk.impact
        assert risk.status == "active"

    def test_risk_score_accuracy(self, db: Session):
        """Ensure correct risk score calculation"""

        risk_data = schemas_module.RiskCreate(
            risk_title="Test Risk",
            probability=3,
            impact=3,
            department="IT"
        )

        risk = crud.create_risk(db, risk_data)

        assert risk.risk_score == 9

    def test_risk_update(self, db: Session, test_risk):
        """Validate risk update recalculation"""

        update_data = schemas_module.RiskUpdate(
            probability=5,
            impact=5
        )

        updated = crud.update_risk(db, test_risk.id, update_data)

        assert updated.risk_score == 25

    def test_risk_not_found(self, db: Session):
        """Ensure missing risk returns None"""

        result = crud.get_risk(db, 999999)
        assert result is None


# ============================================================
# COMPLIANCE CRUD TESTS
# ============================================================

class TestComplianceCRUD:
    """Compliance module validation"""

    def test_create_policy(self, db: Session):
        """Validate compliance policy creation"""

        policy = schemas_module.ComplianceCreate(
            policy_name="Data Protection Policy",
            department="Legal"
        )

        result = crud.create_compliance_policy(db, policy)

        assert result.id is not None
        assert result.status == "pending"

    def test_update_policy(self, db: Session, test_compliance):
        """Validate policy update"""

        update_data = schemas_module.ComplianceUpdate(
            status="completed"
        )

        updated = crud.update_compliance_policy(
            db,
            test_compliance.id,
            update_data
        )

        assert updated.status == "completed"


# ============================================================
# INTEGRATION TESTS (REAL-WORLD FLOW)
# ============================================================

class TestIntegrationScenarios:
    """End-to-end business workflow validation"""

    def test_incident_lifecycle(self, db: Session, test_user):
        """Full incident lifecycle test"""

        incident = crud.create_incident(
            db,
            schemas_module.IncidentCreate(
                title="Security Breach",
                description="Unauthorized access detected",
                severity="critical",
                department="Security",
                category="Unauthorized Access"
            )
        )

        assert incident.status == "open"

        updated = crud.update_incident(
            db,
            incident.id,
            schemas_module.IncidentUpdate(status="investigating")
        )

        assert updated.status == "investigating"

    def test_risk_calculation_matrix(self, db: Session):
        """Validate risk scoring matrix correctness"""

        test_cases = [
            (1, 1, 1),
            (2, 3, 6),
            (5, 5, 25),
            (4, 2, 8),
        ]

        for prob, impact, expected in test_cases:
            risk = crud.create_risk(
                db,
                schemas_module.RiskCreate(
                    risk_title=f"Risk {prob}-{impact}",
                    probability=prob,
                    impact=impact,
                    department="Test"
                )
            )

            assert risk.risk_score == expected

    def test_multi_department_isolation(self, db: Session):
        """Ensure department-based isolation works correctly"""

        departments = ["Finance", "IT", "HR", "Legal"]

        for dept in departments:
            crud.create_incident(
                db,
                schemas_module.IncidentCreate(
                    title=f"{dept} Incident",
                    description="Test",
                    severity="medium",
                    department=dept,
                    category="General"
                )
            )

            results = crud.get_incidents_by_department(db, dept)

            assert all(i.department == dept for i in results)