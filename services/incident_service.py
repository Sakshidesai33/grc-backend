# D:\major_project-copy\backend\services\incident_service.py

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# =========================
# Exceptions
# =========================

class IncidentNotFoundError(Exception):
    pass


class IncidentValidationError(Exception):
    pass


# =========================
# Service
# =========================

class IncidentService:
    """Production-grade Incident Service with validation, filtering, and safe DB handling."""

    # Allowed enums (centralized control for consistency)
    ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    ALLOWED_STATUS = {"OPEN", "INVESTIGATING", "MITIGATED", "CLOSED"}

    # =========================
    # Internal Helpers
    # =========================

    @staticmethod
    def _commit(db: Session):
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"DB commit failed: {str(e)}")
            raise

    @staticmethod
    def _validate_incident_payload(data: Dict[str, Any], is_update: bool = False):
        """Validate incident data before DB operations."""
        if not data:
            return

        severity = data.get("severity")
        status = data.get("status")

        if severity and severity not in IncidentService.ALLOWED_SEVERITIES:
            raise IncidentValidationError(f"Invalid severity: {severity}")

        if status and status not in IncidentService.ALLOWED_STATUS:
            raise IncidentValidationError(f"Invalid status: {status}")

        if not is_update:
            if "title" in data and not data["title"].strip():
                raise IncidentValidationError("Title cannot be empty")

            if "description" in data and len(data["description"]) < 10:
                raise IncidentValidationError("Description must be at least 10 characters")

    @staticmethod
    def _apply_update(instance, data: Dict[str, Any]):
        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

    # =========================
    # CRUD Operations
    # =========================

    @staticmethod
    def get_incidents(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get incidents with filtering, pagination, and search.
        Returns structured response for frontend consumption.
        """
        try:
            query = db.query(models.Incident)

            # Filters
            if status:
                query = query.filter(models.Incident.status == status)

            if severity:
                query = query.filter(models.Incident.severity == severity)

            if department:
                query = query.filter(models.Incident.department == department)

            if search:
                like_pattern = f"%{search}%"
                query = query.filter(
                    models.Incident.title.ilike(like_pattern)
                    | models.Incident.description.ilike(like_pattern)
                )

            total = query.count()

            incidents = (
                query.order_by(models.Incident.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

            return {
                "items": incidents,
                "total": total,
                "skip": skip,
                "limit": limit,
            }

        except Exception as e:
            logger.error(f"Error fetching incidents: {str(e)}")
            raise

    @staticmethod
    def get_incident(db: Session, incident_id: int) -> models.Incident:
        try:
            incident = (
                db.query(models.Incident)
                .filter(models.Incident.id == incident_id)
                .first()
            )

            if not incident:
                raise IncidentNotFoundError(f"Incident {incident_id} not found")

            return incident

        except Exception as e:
            logger.error(f"Error fetching incident {incident_id}: {str(e)}")
            raise

    @staticmethod
    def create_incident(db: Session, incident: schemas.IncidentCreate) -> models.Incident:
        try:
            data = incident.model_dump()

            IncidentService._validate_incident_payload(data)

            # Set defaults
            if "status" not in data or not data["status"]:
                data["status"] = "OPEN"

            if "incident_date" not in data or not data["incident_date"]:
                data["incident_date"] = datetime.utcnow()

            db_incident = models.Incident(**data)

            db.add(db_incident)
            IncidentService._commit(db)
            db.refresh(db_incident)

            logger.info(f"Incident created: ID={db_incident.id}")
            return db_incident

        except Exception as e:
            logger.error(f"Error creating incident: {str(e)}")
            raise

    @staticmethod
    def update_incident(
        db: Session,
        incident_id: int,
        incident_update: schemas.IncidentUpdate,
    ) -> models.Incident:
        try:
            db_incident = IncidentService.get_incident(db, incident_id)

            update_data = incident_update.model_dump(exclude_unset=True)

            IncidentService._validate_incident_payload(update_data, is_update=True)

            # Auto timestamp update
            update_data["updated_at"] = datetime.utcnow()

            IncidentService._apply_update(db_incident, update_data)

            IncidentService._commit(db)
            db.refresh(db_incident)

            logger.info(f"Incident updated: ID={incident_id}")
            return db_incident

        except Exception as e:
            logger.error(f"Error updating incident {incident_id}: {str(e)}")
            raise

    @staticmethod
    def delete_incident(db: Session, incident_id: int) -> Dict[str, Any]:
        """
        Deletes incident permanently.
        (Can be upgraded later to soft delete if schema supports it)
        """
        try:
            db_incident = IncidentService.get_incident(db, incident_id)

            db.delete(db_incident)
            IncidentService._commit(db)

            logger.info(f"Incident deleted: ID={incident_id}")

            return {"deleted": True, "incident_id": incident_id}

        except Exception as e:
            logger.error(f"Error deleting incident {incident_id}: {str(e)}")
            raise

    # =========================
    # Domain Queries
    # =========================

    @staticmethod
    def get_incidents_by_department(db: Session, department: str) -> List[models.Incident]:
        try:
            return (
                db.query(models.Incident)
                .filter(models.Incident.department == department)
                .order_by(models.Incident.created_at.desc())
                .all()
            )
        except Exception as e:
            logger.error(f"Error fetching incidents by department: {str(e)}")
            raise

    # =========================
    # Analytics / Stats
    # =========================

    @staticmethod
    def get_incident_statistics(db: Session) -> Dict[str, Any]:
        try:
            total = db.query(models.Incident).count()

            open_incidents = db.query(models.Incident).filter(
                models.Incident.status.in_(["OPEN", "INVESTIGATING", "MITIGATED"])
            ).count()

            # Severity distribution (single query optimization)
            severity_rows = (
                db.query(
                    models.Incident.severity,
                    func.count(models.Incident.id)
                )
                .group_by(models.Incident.severity)
                .all()
            )

            severity_distribution = {
                severity: count for severity, count in severity_rows
            }

            # Ensure all keys exist
            for s in IncidentService.ALLOWED_SEVERITIES:
                severity_distribution.setdefault(s, 0)

            # Department distribution
            dept_rows = (
                db.query(
                    models.Incident.department,
                    func.count(models.Incident.id)
                )
                .group_by(models.Incident.department)
                .all()
            )

            department_distribution = {
                dept or "UNKNOWN": count for dept, count in dept_rows
            }

            return {
                "total_incidents": total,
                "open_incidents": open_incidents,
                "closed_incidents": total - open_incidents,
                "severity_distribution": severity_distribution,
                "department_distribution": department_distribution,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating incident statistics: {str(e)}")
            raise