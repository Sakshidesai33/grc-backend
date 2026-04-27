from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database import get_db
import services.incident_service as incident_service
import schemas
import models

router = APIRouter(prefix="/incidents", tags=["Incidents"])
logger = logging.getLogger(__name__)


def safe_execute(func, *args, default=None):
    try:
        return func(*args)
    except Exception as e:
        logger.error(f"Service error: {str(e)}", exc_info=True)
        return default


@router.get("/", response_model=List[schemas.Incident])
async def get_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get incidents with advanced filtering, pagination & safe querying
    """
    try:
        query = db.query(models.Incident)

        # Flexible filtering (case-insensitive safe)
        if department:
            query = query.filter(models.Incident.department.ilike(f"%{department}%"))

        if severity:
            query = query.filter(models.Incident.severity == severity.upper())

        if status:
            query = query.filter(models.Incident.status == status.upper())

        incidents = (
            query.order_by(models.Incident.incident_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return incidents

    except Exception as e:
        logger.error(f"Fetch incidents failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve incidents"
        )


@router.get("/{incident_id}", response_model=schemas.Incident)
async def get_incident(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Get single incident with full detail view
    """
    try:
        incident = incident_service.IncidentService.get_incident(db, incident_id)

        if not incident:
            raise HTTPException(
                status_code=404,
                detail=f"Incident {incident_id} not found"
            )

        return incident

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get incident failed ({incident_id}): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve incident"
        )


@router.post("/", response_model=schemas.Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident: schemas.IncidentCreate,
    db: Session = Depends(get_db)
):
    """
    Create incident with validation-ready structure
    """
    try:
        # Basic validation safety layer
        if not incident.title or not incident.description:
            raise HTTPException(
                status_code=400,
                detail="Title and description are required"
            )

        created = incident_service.IncidentService.create_incident(db, incident)

        logger.info(f"Incident created: {getattr(created, 'id', 'unknown')}")

        return created

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create incident failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create incident"
        )


@router.put("/{incident_id}", response_model=schemas.Incident)
async def update_incident(
    incident_id: str,
    incident_update: schemas.IncidentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update incident with partial update support
    """
    try:
        updated = incident_service.IncidentService.update_incident(
            db, incident_id, incident_update
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"Incident {incident_id} not found"
            )

        logger.info(f"Incident updated: {incident_id}")

        return updated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update incident failed ({incident_id}): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update incident"
        )


@router.delete("/{incident_id}")
async def delete_incident(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete incident (safe delete with validation hook support)
    """
    try:
        deleted = incident_service.IncidentService.delete_incident(db, incident_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Incident {incident_id} not found"
            )

        logger.info(f"Incident deleted: {incident_id}")

        return {
            "success": True,
            "message": "Incident deleted successfully",
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete incident failed ({incident_id}): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete incident"
        )


@router.get("/statistics")
async def get_incident_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Dashboard-ready incident analytics
    """
    try:
        stats = safe_execute(
            incident_service.IncidentService.get_incident_statistics,
            db,
            default={}
        )

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "total_incidents": stats.get("total_incidents", 0),
                "open_incidents": stats.get("open_incidents", 0),
                "closed_incidents": stats.get("closed_incidents", 0),
                "severity_distribution": stats.get("severity_distribution", {}),
                "status_distribution": stats.get("status_distribution", {}),
                "department_distribution": stats.get("department_distribution", {}),
                "average_resolution_time": stats.get("avg_resolution_time", 0)
            }
        }

    except Exception as e:
        logger.error(f"Statistics fetch failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch incident statistics"
        )


@router.get("/departments")
async def get_departments(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get unique departments with metadata (not just raw list)
    """
    try:
        departments = (
            db.query(models.Incident.department)
            .filter(models.Incident.department.isnot(None))
            .distinct()
            .all()
        )

        dept_list = sorted([d[0] for d in departments if d[0]])

        return {
            "success": True,
            "count": len(dept_list),
            "departments": dept_list,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Departments fetch failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch departments"
        )   