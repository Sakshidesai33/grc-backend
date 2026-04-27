from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from database import get_db
from services.incident_service import IncidentService
from services.risk_service import RiskService
from services.compliance_service import ComplianceService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# =========================
# DASHBOARD ANALYTICS
# =========================
@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Unified dashboard analytics for GRC system.
    Combines Incident, Risk, and Compliance insights.
    """
    try:
        incident_stats = IncidentService.get_incident_statistics(db)
        risk_stats = RiskService.get_risk_statistics(db)
        compliance_stats = ComplianceService.get_compliance_dashboard(db)

        return {
            "success": True,
            "data": {
                "incidents": incident_stats,
                "risks": risk_stats,
                "compliance": compliance_stats,
                "summary": {
                    "total_incidents": incident_stats.get("total_incidents", 0),
                    "open_incidents": incident_stats.get("open_incidents", 0),
                    "critical_risks": risk_stats.get("critical_risks", 0),
                    "high_risk_items": risk_stats.get("high_risk_items", 0),
                    "compliance_score": compliance_stats.get("compliance_score", 0.0),
                    "overall_health_score": _calculate_health_score(
                        incident_stats, risk_stats, compliance_stats
                    )
                }
            },
            "message": "Dashboard analytics fetched successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard analytics failed: {str(e)}"
        )


# =========================
# INCIDENT TRENDS
# =========================
@router.get("/trends", response_model=Dict[str, Any])
async def get_incident_trends(
    db: Session = Depends(get_db),
    period: str = Query("12m", description="Time period: 6m, 12m, 24m")
):
    """
    Incident trends over time with severity breakdown.
    """
    try:
        # In production → replace with DB aggregation by date
        return {
            "success": True,
            "data": {
                "period": period,
                "monthly_trends": {
                    "2025-01": 12,
                    "2025-02": 18,
                    "2025-03": 14,
                    "2025-04": 22,
                    "2025-05": 17,
                    "2025-06": 20,
                    "2025-07": 15,
                    "2025-08": 19,
                    "2025-09": 16,
                    "2025-10": 21,
                    "2025-11": 18,
                    "2025-12": 14
                },
                "severity_trends": {
                    "CRITICAL": [5, 8, 6, 9, 7, 8, 6, 5, 9, 7, 8, 6],
                    "HIGH": [8, 12, 9, 11, 10, 12, 9, 11, 10, 12, 9, 8],
                    "MEDIUM": [15, 18, 16, 14, 17, 15, 16, 14, 17, 15, 16, 15],
                    "LOW": [10, 8, 12, 9, 11, 10, 12, 9, 8, 10, 9, 8]
                }
            },
            "message": "Trend analysis completed"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# REPORT GENERATION
# =========================
@router.get("/reports", response_model=Dict[str, Any])
async def generate_reports(db: Session = Depends(get_db)):
    """
    Generate consolidated GRC analytics report.
    """
    try:
        incident_stats = IncidentService.get_incident_statistics(db)
        risk_stats = RiskService.get_risk_statistics(db)
        compliance_stats = ComplianceService.get_compliance_dashboard(db)

        return {
            "success": True,
            "data": {
                "incident_report": {
                    "total": incident_stats.get("total_incidents", 0),
                    "by_severity": incident_stats.get("severity_distribution", {}),
                    "open": incident_stats.get("open_incidents", 0),
                    "resolution_rate": incident_stats.get("resolution_rate", 0.0)
                },
                "risk_report": {
                    "total": risk_stats.get("total_risks", 0),
                    "by_level": risk_stats.get("risk_distribution", {}),
                    "high_risks": risk_stats.get("high_risk_items", 0),
                    "avg_risk_score": risk_stats.get("avg_risk_score", 0)
                },
                "compliance_report": {
                    "total_policies": compliance_stats.get("total_policies", 0),
                    "compliance_rate": compliance_stats.get("compliance_score", 0.0),
                    "compliant": compliance_stats.get("compliant", 0),
                    "non_compliant": compliance_stats.get("non_compliant", 0),
                    "pending_review": compliance_stats.get("pending_review", 0)
                }
            },
            "message": "Reports generated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# HEALTH SCORE CALCULATION
# =========================
def _calculate_health_score(incidents: dict, risks: dict, compliance: dict) -> float:
    """
    Internal: Compute overall system health score (0–100)
    """
    try:
        incident_score = max(0, 100 - incidents.get("open_incidents", 0) * 2)
        risk_score = max(0, 100 - risks.get("high_risk_items", 0) * 5)
        compliance_score = compliance.get("compliance_score", 0)

        return round(
            (incident_score * 0.4) +
            (risk_score * 0.4) +
            (compliance_score * 0.2),
            2
        )
    except Exception:
        return 0.0