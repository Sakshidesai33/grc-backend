from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from database import get_db
import services.incident_service as incident_service
import services.risk_service as risk_service
import services.compliance_service as compliance_service

# Logger setup
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def safe_get_stats(func, db: Session, default: Dict[str, Any]):
    """Wrapper to safely execute service calls"""
    try:
        result = func(db)
        return result if result else default
    except Exception as e:
        logger.error(f"Analytics service error in {func.__name__}: {str(e)}")
        return default


@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Get comprehensive dashboard analytics across incidents, risks, and compliance
    """
    try:
        incident_stats = safe_get_stats(
            incident_service.IncidentService.get_incident_statistics,
            db,
            {}
        )

        risk_stats = safe_get_stats(
            risk_service.RiskService.get_risk_statistics,
            db,
            {}
        )

        compliance_stats = safe_get_stats(
            compliance_service.ComplianceService.get_compliance_dashboard,
            db,
            {}
        )

        summary = {
            "total_incidents": incident_stats.get("total_incidents", 0),
            "open_incidents": incident_stats.get("open_incidents", 0),
            "high_risk_items": risk_stats.get("high_risk_items", 0),
            "compliance_score": compliance_stats.get("compliance_score", 0.0)
        }

        return {
            "success": True,
            "data": {
                "incidents": incident_stats,
                "risks": risk_stats,
                "compliance": compliance_stats,
                "summary": summary
            }
        }

    except Exception as e:
        logger.exception("Failed to fetch dashboard analytics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard analytics"
        )


@router.get("/trends", status_code=status.HTTP_200_OK)
async def get_incident_trends(db: Session = Depends(get_db)):
    """
    Get incident trends over time (mock + safe production structure)
    """
    try:
        # In production: replace with DB aggregation query or analytics service
        monthly_trends = {
            "2024-01": 12,
            "2024-02": 18,
            "2024-03": 14,
            "2024-04": 22,
            "2024-05": 17,
            "2024-06": 20,
            "2024-07": 15,
            "2024-08": 19,
            "2024-09": 16,
            "2024-10": 21,
            "2024-11": 18,
            "2024-12": 14
        }

        severity_trends = {
            "CRITICAL": [5, 8, 6, 9, 7, 8, 6, 5, 9, 7, 8, 6],
            "HIGH": [8, 12, 9, 11, 10, 12, 9, 11, 10, 12, 9, 8],
            "MEDIUM": [15, 18, 16, 14, 17, 15, 16, 14, 17, 15, 16, 15],
            "LOW": [10, 8, 12, 9, 11, 10, 12, 9, 8, 10, 9, 8]
        }

        return {
            "success": True,
            "data": {
                "monthly_trends": monthly_trends,
                "severity_trends": severity_trends
            }
        }

    except Exception as e:
        logger.exception("Failed to fetch incident trends")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch incident trends"
        )


@router.get("/reports", status_code=status.HTTP_200_OK)
async def get_analytics_reports(db: Session = Depends(get_db)):
    """
    Generate consolidated analytics report
    """
    try:
        incident_stats = safe_get_stats(
            incident_service.IncidentService.get_incident_statistics,
            db,
            {}
        )

        risk_stats = safe_get_stats(
            risk_service.RiskService.get_risk_statistics,
            db,
            {}
        )

        compliance_stats = safe_get_stats(
            compliance_service.ComplianceService.get_compliance_dashboard,
            db,
            {}
        )

        report = {
            "incident_summary": {
                "total": incident_stats.get("total_incidents", 0),
                "by_severity": incident_stats.get("severity_distribution", {}),
                "open_vs_closed": {
                    "open": incident_stats.get("open_incidents", 0),
                    "closed": (
                        incident_stats.get("total_incidents", 0)
                        - incident_stats.get("open_incidents", 0)
                    )
                }
            },
            "risk_summary": {
                "total": risk_stats.get("total_risks", 0),
                "by_level": risk_stats.get("risk_distribution", {}),
                "high_priority": risk_stats.get("high_risk_items", 0)
            },
            "compliance_summary": {
                "total_policies": compliance_stats.get("total_policies", 0),
                "compliance_rate": compliance_stats.get("compliance_score", 0.0),
                "status_breakdown": {
                    "compliant": compliance_stats.get("compliant", 0),
                    "non_compliant": compliance_stats.get("non_compliant", 0),
                    "pending": compliance_stats.get("pending_review", 0)
                }
            }
        }

        return {
            "success": True,
            "data": report
        }

    except Exception as e:
        logger.exception("Failed to generate analytics report")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics report"
        )