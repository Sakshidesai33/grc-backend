from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

import models
import schemas

logger = logging.getLogger(__name__)


class IncidentService:
    """
    Production-grade Incident Service
    - Centralized validation
    - Safe updates
    - Audit-friendly operations
    - Extensible for AI/analytics integration
    """

    # ----------------------------
    # INTERNAL HELPERS
    # ----------------------------

    @staticmethod
    def _validate_incident_data(data: Dict[str, Any]) -> None:
        """Basic validation layer to ensure data integrity"""
        if not data:
            raise ValueError("Incident data cannot be empty")

        if "title" in data and not data["title"]:
            raise ValueError("Incident title cannot be empty")

        if "severity" in data:
            allowed = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
            if data["severity"] not in allowed:
                raise ValueError(f"Invalid severity: {data['severity']}")

        if "status" in data:
            allowed = {"OPEN", "INVESTIGATING", "MITIGATED", "CLOSED"}
            if data["status"] not in allowed:
                raise ValueError(f"Invalid status: {data['status']}")

    @staticmethod
    def _get_incident_or_raise(db: Session, incident_id: int) -> models.Incident:
        incident = (
            db.query(models.Incident)
            .filter(models.Incident.id == incident_id)
            .first()
        )
        if not incident:
            raise ValueError(f"Incident with id {incident_id} not found")
        return incident

    @staticmethod
    def _commit(db: Session) -> None:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"DB commit failed: {str(e)}")
            raise

    # ----------------------------
    # CRUD OPERATIONS
    # ----------------------------

    @staticmethod
    def get_incidents(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        department: Optional[str] = None,
    ) -> List[models.Incident]:
        """
        Optimized incident retrieval with filters
        """
        query = db.query(models.Incident)

        if status:
            query = query.filter(models.Incident.status == status)

        if severity:
            query = query.filter(models.Incident.severity == severity)

        if department:
            query = query.filter(models.Incident.department == department)

        return (
            query.order_by(models.Incident.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_incident(db: Session, incident_id: int) -> Optional[models.Incident]:
        return (
            db.query(models.Incident)
            .filter(models.Incident.id == incident_id)
            .first()
        )

    @staticmethod
    def create_incident(
        db: Session, incident: schemas.IncidentCreate
    ) -> models.Incident:
        """
        Create incident with validation + audit fields
        """
        try:
            data = incident.model_dump()
            IncidentService._validate_incident_data(data)

            db_incident = models.Incident(
                **data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status=data.get("status", "OPEN"),
            )

            db.add(db_incident)
            IncidentService._commit(db)
            db.refresh(db_incident)

            logger.info(f"Incident created: ID={db_incident.id}")
            return db_incident

        except Exception as e:
            logger.error(f"Create incident failed: {str(e)}")
            raise

    @staticmethod
    def update_incident(
        db: Session, incident_id: int, incident_update: schemas.IncidentUpdate
    ) -> models.Incident:
        """
        Partial update with safe field handling
        """
        try:
            db_incident = IncidentService._get_incident_or_raise(db, incident_id)

            update_data = incident_update.model_dump(exclude_unset=True)
            IncidentService._validate_incident_data(update_data)

            for field, value in update_data.items():
                if hasattr(db_incident, field):
                    setattr(db_incident, field, value)

            db_incident.updated_at = datetime.utcnow()

            IncidentService._commit(db)
            db.refresh(db_incident)

            logger.info(f"Incident updated: ID={incident_id}")
            return db_incident

        except Exception as e:
            logger.error(f"Update incident failed: {str(e)}")
            raise

    @staticmethod
    def delete_incident(db: Session, incident_id: int) -> bool:
        """
        Safe delete with existence check
        """
        try:
            db_incident = IncidentService._get_incident_or_raise(db, incident_id)

            db.delete(db_incident)
            IncidentService._commit(db)

            logger.info(f"Incident deleted: ID={incident_id}")
            return True

        except Exception as e:
            logger.error(f"Delete incident failed: {str(e)}")
            raise

    # ----------------------------
    # DOMAIN QUERIES
    # ----------------------------

    @staticmethod
    def get_incidents_by_department(
        db: Session, department: str, limit: int = 100
    ) -> List[models.Incident]:
        return (
            db.query(models.Incident)
            .filter(models.Incident.department == department)
            .order_by(models.Incident.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_incidents_by_status(
        db: Session, status: str, limit: int = 100
    ) -> List[models.Incident]:
        return (
            db.query(models.Incident)
            .filter(models.Incident.status == status)
            .order_by(models.Incident.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_recent_incidents(
        db: Session, days: int = 7, limit: int = 100
    ) -> List[models.Incident]:
        cutoff = datetime.utcnow() - datetime.timedelta(days=days)

        return (
            db.query(models.Incident)
            .filter(models.Incident.created_at >= cutoff)
            .order_by(models.Incident.created_at.desc())
            .limit(limit)
            .all()
        )

    # ----------------------------
    # STATISTICS & ANALYTICS
    # ----------------------------

    @staticmethod
    def get_incident_statistics(db: Session) -> Dict[str, Any]:
        """
        Production-ready aggregated statistics
        """
        try:
            total = db.query(models.Incident).count()

            open_incidents = (
                db.query(models.Incident)
                .filter(models.Incident.status.in_(["OPEN", "INVESTIGATING"]))
                .count()
            )

            resolved = (
                db.query(models.Incident)
                .filter(models.Incident.status == "CLOSED")
                .count()
            )

            severity_counts = {}
            for severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                severity_counts[severity] = (
                    db.query(models.Incident)
                    .filter(models.Incident.severity == severity)
                    .count()
                )

            department_counts = (
                db.query(models.Incident.department, db.func.count(models.Incident.id))
                .group_by(models.Incident.department)
                .all()
            )

            return {
                "total_incidents": total,
                "open_incidents": open_incidents,
                "resolved_incidents": resolved,
                "resolution_rate": (resolved / total * 100) if total else 0,
                "severity_distribution": severity_counts,
                "department_distribution": dict(department_counts),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Stats generation failed: {str(e)}")
            return {
                "error": str(e),
                "total_incidents": 0,
                "open_incidents": 0,
                "resolved_incidents": 0,
            }

    # ----------------------------
    # WORKFLOW OPERATIONS
    # ----------------------------

    @staticmethod
    def assign_incident(
        db: Session, incident_id: int, assignee: str
    ) -> models.Incident:
        """
        Assign incident to a user/team
        """
        try:
            incident = IncidentService._get_incident_or_raise(db, incident_id)

            incident.assigned_to = assignee
            incident.status = "INVESTIGATING"
            incident.updated_at = datetime.utcnow()

            IncidentService._commit(db)
            db.refresh(incident)

            logger.info(f"Incident {incident_id} assigned to {assignee}")
            return incident

        except Exception as e:
            logger.error(f"Assignment failed: {str(e)}")
            raise

    @staticmethod
    def resolve_incident(db: Session, incident_id: int) -> models.Incident:
        """
        Mark incident as resolved
        """
        try:
            incident = IncidentService._get_incident_or_raise(db, incident_id)

            incident.status = "CLOSED"
            incident.resolved_at = datetime.utcnow()
            incident.updated_at = datetime.utcnow()

            IncidentService._commit(db)
            db.refresh(incident)

            logger.info(f"Incident resolved: ID={incident_id}")
            return incident

        except Exception as e:
            logger.error(f"Resolve incident failed: {str(e)}")
            raise