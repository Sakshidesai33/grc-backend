from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from database import get_db
import services.incident_service as incident_service
import services.risk_service as risk_service
import services.compliance_service as compliance_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


def safe_execute(func, *args, default=None, error_message="Service execution failed"):
    """Safe wrapper for service calls"""
    try:
        return func(*args)
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exc_info=True)
        return default if default is not None else {}


def safe_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


@router.get("/dashboard")
async def get_dashboard_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive analytics dashboard combining incidents, risks, and compliance metrics
    """
    try:
        incident_stats = safe_execute(
            incident_service.IncidentService.get_incident_statistics,
            db,
            default={}
        )

        risk_stats = safe_execute(
            risk_service.RiskService.get_risk_statistics,
            db,
            default={}
        )

        compliance_stats = safe_execute(
            compliance_service.ComplianceService.get_compliance_dashboard,
            db,
            default={}
        )

        summary = {
            "total_incidents": safe_int(incident_stats.get("total_incidents")),
            "open_incidents": safe_int(incident_stats.get("open_incidents")),
            "high_risk_items": safe_int(risk_stats.get("high_risk_items")),
            "compliance_score": safe_float(compliance_stats.get("compliance_score")),
            "overall_health_score": round(
                (
                    (100 - safe_float(compliance_stats.get("compliance_score"))) +
                    max(0, 100 - safe_int(incident_stats.get("open_incidents"))) +
                    max(0, 100 - safe_int(risk_stats.get("high_risk_items")) * 5)
                ) / 3,
                2
            )
        }

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "incidents": incident_stats,
            "risks": risk_stats,
            "compliance": compliance_stats,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Dashboard analytics failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate dashboard analytics"
        )


@router.get("/trends")
async def get_incident_trends(
    db: Session = Depends(get_db),
    days: int = Query(180, ge=30, le=365)
) -> Dict[str, Any]:
    """
    Get incident trends over time (dynamic range-based analytics)
    """
    try:
        # Try service-based trend extraction first
        if hasattr(incident_service.IncidentService, "get_incident_trends"):
            trends = incident_service.IncidentService.get_incident_trends(db, days)
        else:
            # Fallback: structured placeholder derived from DB stats (not fake static data)
            cutoff = datetime.utcnow() - timedelta(days=days)

            base_stats = safe_execute(
                incident_service.IncidentService.get_incident_statistics,
                db,
                default={}
            )

            total = safe_int(base_stats.get("total_incidents"))

            trends = {
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_incidents": total,
                    "avg_daily_incidents": round(total / max(days, 1), 2)
                },
                "note": "Trend aggregation requires time-series query implementation in service layer"
            }

        return {
            "success": True,
            "data": trends
        }

    except Exception as e:
        logger.error(f"Trend analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch incident trends"
        )


@router.get("/reports")
async def get_analytics_reports(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Generate consolidated analytics report across incidents, risks, and compliance
    """
    try:
        incident_stats = safe_execute(
            incident_service.IncidentService.get_incident_statistics,
            db,
            default={}
        )

        risk_stats = safe_execute(
            risk_service.RiskService.get_risk_statistics,
            db,
            default={}
        )

        compliance_stats = safe_execute(
            compliance_service.ComplianceService.get_compliance_dashboard,
            db,
            default={}
        )

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "incident_summary": {
                "total": safe_int(incident_stats.get("total_incidents")),
                "open": safe_int(incident_stats.get("open_incidents")),
                "closed": max(
                    0,
                    safe_int(incident_stats.get("total_incidents")) -
                    safe_int(incident_stats.get("open_incidents"))
                ),
                "severity_distribution": incident_stats.get("severity_distribution", {})
            },
            "risk_summary": {
                "total": safe_int(risk_stats.get("total_risks")),
                "by_level": risk_stats.get("risk_distribution", {}),
                "high_priority": safe_int(risk_stats.get("high_risk_items"))
            },
            "compliance_summary": {
                "total_policies": safe_int(compliance_stats.get("total_policies")),
                "compliance_rate": safe_float(compliance_stats.get("compliance_score")),
                "status_breakdown": {
                    "compliant": safe_int(compliance_stats.get("compliant")),
                    "non_compliant": safe_int(compliance_stats.get("non_compliant")),
                    "pending": safe_int(compliance_stats.get("pending_review"))
                }
            },
            "risk_indicators": {
                "incident_risk_ratio": round(
                    safe_int(risk_stats.get("total_risks")) /
                    max(safe_int(incident_stats.get("total_incidents")), 1),
                    3
                )
            }
        }

        return {
            "success": True,
            "data": report
        }

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate analytics report"
        )