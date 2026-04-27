from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from database import get_db

import services.incident_service as incident_service
import services.risk_service as risk_service
import services.compliance_service as compliance_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ================================
# CORE DASHBOARD ANALYTICS
# ================================
@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Returns unified analytics for dashboard UI:
    - Incident KPIs
    - Risk KPIs
    - Compliance KPIs
    - Aggregated system summary
    """

    try:
        incident_stats = incident_service.IncidentService.get_incident_statistics(db)
        risk_stats = risk_service.RiskService.get_risk_statistics(db)
        compliance_stats = compliance_service.ComplianceService.get_compliance_dashboard(db)

        summary = {
            "total_incidents": incident_stats.get("total_incidents", 0),
            "open_incidents": incident_stats.get("open_incidents", 0),
            "critical_incidents": incident_stats.get("severity_distribution", {}).get("CRITICAL", 0),

            "total_risks": risk_stats.get("total_risks", 0),
            "high_risk_items": risk_stats.get("high_risk_items", 0),

            "compliance_score": compliance_stats.get("compliance_score", 0.0),
            "non_compliant_items": compliance_stats.get("non_compliant", 0),
        }

        return {
            "success": True,
            "data": {
                "incidents": incident_stats,
                "risks": risk_stats,
                "compliance": compliance_stats,
                "summary": summary
            },
            "message": "Dashboard analytics fetched successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard analytics: {str(e)}"
        )


# ================================
# INCIDENT & RISK TRENDS
# ================================
@router.get("/trends", response_model=Dict[str, Any])
async def get_trends(db: Session = Depends(get_db)):
    """
    Returns time-series analytics for charts:
    - Incident trends
    - Severity trends
    - Risk trend readiness (future ML integration point)
    """

    try:
        incident_trends = incident_service.IncidentService.get_incident_trends(db)
        risk_trends = risk_service.RiskService.get_risk_trends(db, days=30)

        return {
            "success": True,
            "data": {
                "incident_trends": incident_trends,
                "risk_trends": risk_trends
            },
            "message": "Trend analytics generated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trends: {str(e)}"
        )


# ================================
# REPORTING ENGINE
# ================================
@router.get("/reports", response_model=Dict[str, Any])
async def get_analytics_reports(db: Session = Depends(get_db)):
    """
    Enterprise reporting layer:
    - Incident summary
    - Risk summary
    - Compliance summary
    """

    try:
        incident_stats = incident_service.IncidentService.get_incident_statistics(db)
        risk_stats = risk_service.RiskService.get_risk_statistics(db)
        compliance_stats = compliance_service.ComplianceService.get_compliance_dashboard(db)

        report = {
            "incident_summary": {
                "total": incident_stats.get("total_incidents", 0),
                "by_severity": incident_stats.get("severity_distribution", {}),
                "open": incident_stats.get("open_incidents", 0),
                "closed": incident_stats.get("closed_incidents", 0),
            },
            "risk_summary": {
                "total": risk_stats.get("total_risks", 0),
                "by_level": risk_stats.get("risk_distribution", {}),
                "high_priority": risk_stats.get("high_risk_items", 0),
            },
            "compliance_summary": {
                "total_policies": compliance_stats.get("total_policies", 0),
                "compliance_score": compliance_stats.get("compliance_score", 0.0),
                "compliant": compliance_stats.get("compliant", 0),
                "non_compliant": compliance_stats.get("non_compliant", 0),
                "pending_review": compliance_stats.get("pending_review", 0),
            }
        }

        return {
            "success": True,
            "data": report,
            "message": "Analytics report generated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


# ================================
# REAL-TIME INSIGHT ENDPOINT
# ================================
@router.get("/insights", response_model=Dict[str, Any])
async def get_real_time_insights(db: Session = Depends(get_db)):
    """
    AI-ready insights endpoint (future ML + anomaly detection integration)
    """

    try:
        incident_stats = incident_service.IncidentService.get_incident_statistics(db)
        risk_stats = risk_service.RiskService.get_risk_statistics(db)

        insights = {
            "risk_alert": risk_stats.get("high_risk_items", 0) > 5,
            "incident_spike": incident_stats.get("open_incidents", 0) > 20,
            "system_health": "CRITICAL" if risk_stats.get("high_risk_items", 0) > 10 else "STABLE",
        }

        return {
            "success": True,
            "data": insights,
            "message": "Real-time insights generated"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )