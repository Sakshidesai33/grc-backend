from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database import get_db
import services.compliance_service as compliance_service
import schemas
import models

router = APIRouter(prefix="/compliance", tags=["Compliance"])
logger = logging.getLogger(__name__)


def safe_execute(func, *args, default=None, error_message="Compliance service error"):
    try:
        return func(*args)
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exc_info=True)
        return default


@router.get("/", response_model=List[schemas.Compliance])
async def get_compliance_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all compliance policies with filtering, pagination, and validation
    """
    try:
        query = db.query(models.CompliancePolicy)

        # Safe filtering
        if department:
            query = query.filter(models.CompliancePolicy.department.ilike(f"%{department}%"))

        if status:
            query = query.filter(models.CompliancePolicy.compliance_status == status)

        policies = (
            query.order_by(models.CompliancePolicy.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return policies

    except Exception as e:
        logger.error(f"Failed to fetch compliance policies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve compliance policies"
        )


@router.get("/{policy_id}", response_model=schemas.Compliance)
async def get_compliance_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    Get single compliance policy by ID
    """
    try:
        policy = compliance_service.ComplianceService.get_compliance_policy(db, policy_id)

        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"Compliance policy with ID {policy_id} not found"
            )

        return policy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching policy {policy_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve compliance policy"
        )


@router.post("/", response_model=schemas.Compliance, status_code=status.HTTP_201_CREATED)
async def create_compliance_policy(
    policy: schemas.ComplianceCreate,
    db: Session = Depends(get_db)
):
    """
    Create new compliance policy with validation and audit-ready structure
    """
    try:
        # basic validation safety layer
        if not policy.policy_name:
            raise HTTPException(status_code=400, detail="Policy name is required")

        created_policy = compliance_service.ComplianceService.create_compliance_policy(db, policy)

        logger.info(f"Compliance policy created: {created_policy.id}")

        return created_policy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create compliance policy"
        )


@router.put("/{policy_id}", response_model=schemas.Compliance)
async def update_compliance_policy(
    policy_id: int,
    policy_update: schemas.ComplianceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update compliance policy with safe partial updates
    """
    try:
        updated_policy = compliance_service.ComplianceService.update_compliance_policy(
            db, policy_id, policy_update
        )

        if not updated_policy:
            raise HTTPException(
                status_code=404,
                detail=f"Compliance policy {policy_id} not found"
            )

        logger.info(f"Compliance policy updated: {policy_id}")

        return updated_policy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy update failed ({policy_id}): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update compliance policy"
        )


@router.delete("/{policy_id}")
async def delete_compliance_policy(
    policy_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete compliance policy (soft-safe pattern recommended in real systems)
    """
    try:
        policy = compliance_service.ComplianceService.get_compliance_policy(db, policy_id)

        if not policy:
            raise HTTPException(
                status_code=404,
                detail="Compliance policy not found"
            )

        db.delete(policy)
        db.commit()

        logger.info(f"Compliance policy deleted: {policy_id}")

        return {
            "success": True,
            "message": "Compliance policy deleted successfully",
            "deleted_id": policy_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Policy deletion failed ({policy_id}): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete compliance policy"
        )


@router.get("/dashboard")
async def get_compliance_dashboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Compliance dashboard with real-time metrics
    """
    try:
        dashboard = safe_execute(
            compliance_service.ComplianceService.get_compliance_dashboard,
            db,
            default={}
        )

        # Normalize structure for frontend stability
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "total_policies": dashboard.get("total_policies", 0),
                "compliance_score": dashboard.get("compliance_score", 0.0),
                "compliant": dashboard.get("compliant", 0),
                "non_compliant": dashboard.get("non_compliant", 0),
                "pending_review": dashboard.get("pending_review", 0),
                "risk_exposure": dashboard.get("risk_exposure", "MEDIUM"),
                "department_wise": dashboard.get("department_wise", {})
            }
        }

    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to load compliance dashboard"
        )


@router.get("/upcoming-audits")
async def get_upcoming_audits(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get upcoming audits with configurable time window
    """
    try:
        audits = safe_execute(
            compliance_service.ComplianceService.get_upcoming_audits,
            db,
            default=[]
        )

        return {
            "success": True,
            "window_days": days,
            "count": len(audits) if audits else 0,
            "data": audits,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Audit fetch failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve upcoming audits"
        )