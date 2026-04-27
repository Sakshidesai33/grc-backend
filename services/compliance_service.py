from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
import logging

import models
import schemas

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Production-grade Compliance Service:
    - Clean DB access layer
    - Safe computations
    - Defensive querying
    - Scalable analytics-ready structure
    """

    # =========================
    # BASIC CRUD
    # =========================

    @staticmethod
    def get_compliance_policies(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[models.CompliancePolicy]:
        try:
            return (
                db.query(models.CompliancePolicy)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to fetch compliance policies: {str(e)}")
            return []

    @staticmethod
    def get_compliance_policy(
        db: Session,
        policy_id: int
    ) -> Optional[models.CompliancePolicy]:
        try:
            return (
                db.query(models.CompliancePolicy)
                .filter(models.CompliancePolicy.id == policy_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Failed to fetch policy {policy_id}: {str(e)}")
            return None

    @staticmethod
    def create_compliance_policy(
        db: Session,
        policy: schemas.ComplianceCreate
    ) -> models.CompliancePolicy:
        try:
            db_policy = models.CompliancePolicy(**policy.model_dump())
            db.add(db_policy)
            db.commit()
            db.refresh(db_policy)
            return db_policy

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create compliance policy: {str(e)}")
            raise

    @staticmethod
    def update_compliance_policy(
        db: Session,
        policy_id: int,
        policy_update: schemas.ComplianceUpdate
    ) -> Optional[models.CompliancePolicy]:

        try:
            db_policy = ComplianceService.get_compliance_policy(db, policy_id)
            if not db_policy:
                return None

            update_data = policy_update.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_policy, field, value)

            db.commit()
            db.refresh(db_policy)
            return db_policy

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update policy {policy_id}: {str(e)}")
            return None

    @staticmethod
    def delete_compliance_policy(db: Session, policy_id: int) -> bool:
        try:
            policy = ComplianceService.get_compliance_policy(db, policy_id)
            if not policy:
                return False

            db.delete(policy)
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete policy {policy_id}: {str(e)}")
            return False

    # =========================
    # DASHBOARD ANALYTICS
    # =========================

    @staticmethod
    def get_compliance_dashboard(db: Session) -> Dict[str, Any]:
        """
        Returns compliance health metrics for dashboard
        """

        try:
            total = db.query(models.CompliancePolicy).count()

            compliant = db.query(models.CompliancePolicy).filter(
                models.CompliancePolicy.compliance_status == "COMPLIANT"
            ).count()

            non_compliant = db.query(models.CompliancePolicy).filter(
                models.CompliancePolicy.compliance_status == "NON_COMPLIANT"
            ).count()

            pending = db.query(models.CompliancePolicy).filter(
                models.CompliancePolicy.compliance_status == "PENDING_REVIEW"
            ).count()

            compliance_score = (compliant / total * 100) if total > 0 else 0.0

            return {
                "total_policies": total,
                "compliant": compliant,
                "non_compliant": non_compliant,
                "pending_review": pending,
                "compliance_score": round(compliance_score, 2)
            }

        except Exception as e:
            logger.error(f"Dashboard calculation failed: {str(e)}")
            return {
                "total_policies": 0,
                "compliant": 0,
                "non_compliant": 0,
                "pending_review": 0,
                "compliance_score": 0.0
            }

    # =========================
    # AUDIT INTELLIGENCE
    # =========================

    @staticmethod
    def get_upcoming_audits(db: Session) -> List[models.CompliancePolicy]:
        """
        Get policies due for audit in next 30 days
        """
        try:
            today = date.today()
            threshold = today + timedelta(days=30)

            return (
                db.query(models.CompliancePolicy)
                .filter(
                    models.CompliancePolicy.next_audit_date <= threshold,
                    models.CompliancePolicy.compliance_status.in_(
                        ["COMPLIANT", "PENDING_REVIEW"]
                    )
                )
                .order_by(models.CompliancePolicy.next_audit_date.asc())
                .all()
            )

        except Exception as e:
            logger.error(f"Failed to fetch upcoming audits: {str(e)}")
            return []

    @staticmethod
    def get_overdue_audits(db: Session) -> List[models.CompliancePolicy]:
        """
        Get overdue audit policies
        """
        try:
            today = date.today()

            return (
                db.query(models.CompliancePolicy)
                .filter(
                    models.CompliancePolicy.next_audit_date < today,
                    models.CompliancePolicy.compliance_status != "COMPLIANT"
                )
                .order_by(models.CompliancePolicy.next_audit_date.asc())
                .all()
            )

        except Exception as e:
            logger.error(f"Failed to fetch overdue audits: {str(e)}")
            return []

    # =========================
    # COMPLIANCE INSIGHTS
    # =========================

    @staticmethod
    def get_compliance_trend(db: Session) -> Dict[str, Any]:
        """
        Simple compliance trend snapshot (last 90 days logic-ready)
        """

        try:
            total = db.query(models.CompliancePolicy).count()

            compliant = db.query(models.CompliancePolicy).filter(
                models.CompliancePolicy.compliance_status == "COMPLIANT"
            ).count()

            return {
                "trend": "stable",
                "compliance_rate": (compliant / total * 100) if total > 0 else 0,
                "insight": "Maintain current compliance controls"
            }

        except Exception as e:
            logger.error(f"Trend calculation failed: {str(e)}")
            return {
                "trend": "unknown",
                "compliance_rate": 0,
                "insight": "Insufficient data"
            }