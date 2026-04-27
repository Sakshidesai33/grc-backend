from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from collections import defaultdict

import models
import schemas
from models import Risk, RiskMitigation, IncidentRisk, RiskHistory, RiskComment, Incident

logger = logging.getLogger(__name__)


class RiskService:
    """
    Production-grade Risk Management Service
    - Risk lifecycle management
    - Incident linking & dynamic scoring
    - Mitigation tracking
    - Analytics & reporting
    - Audit history tracking
    """

    # =========================
    # CONFIG / CONSTANTS
    # =========================

    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    INCIDENT_SEVERITY_WEIGHT = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    # =========================
    # UTILITIES
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
    def _calculate_risk_level(score: float) -> str:
        if score >= 16:
            return "CRITICAL"
        if score >= 12:
            return "HIGH"
        if score >= 6:
            return "MEDIUM"
        return "LOW"

    # =========================
    # BASIC CRUD
    # =========================

    @staticmethod
    def get_risks(db: Session, skip: int = 0, limit: int = 100, filters: dict = None) -> List[Risk]:
        try:
            query = db.query(Risk).filter(Risk.is_active == True)

            if filters:
                if filters.get("department"):
                    query = query.filter(Risk.department == filters["department"])
                if filters.get("risk_level"):
                    query = query.filter(Risk.risk_level == filters["risk_level"])
                if filters.get("category"):
                    query = query.filter(Risk.category == filters["category"])
                if filters.get("owner_id"):
                    query = query.filter(Risk.owner_id == filters["owner_id"])
                if filters.get("approval_status"):
                    query = query.filter(Risk.approval_status == filters["approval_status"])
                if filters.get("monitoring_status"):
                    query = query.filter(Risk.monitoring_status == filters["monitoring_status"])

            return query.offset(skip).limit(limit).all()

        except Exception as e:
            logger.error(f"get_risks failed: {str(e)}")
            return []

    @staticmethod
    def get_risk(db: Session, risk_id: int) -> Optional[Risk]:
        try:
            return db.query(Risk).filter(Risk.id == risk_id, Risk.is_active == True).first()
        except Exception as e:
            logger.error(f"get_risk failed: {str(e)}")
            return None

    @staticmethod
    def create_risk(db: Session, risk: schemas.RiskCreate, created_by_id: int = None) -> Risk:
        try:
            score = float(risk.probability) * float(risk.impact)
            level = RiskService._calculate_risk_level(score)

            db_risk = Risk(
                **risk.model_dump(),
                risk_score=score,
                risk_level=level,
                last_updated_by_id=created_by_id,
                created_at=datetime.utcnow(),
                is_active=True,
            )

            db.add(db_risk)
            RiskService._commit(db)
            db.refresh(db_risk)

            RiskService._log_risk_change(
                db,
                db_risk.id,
                created_by_id,
                new_score=score,
                new_level=level,
                reason="Risk created",
            )

            return db_risk

        except Exception as e:
            logger.error(f"create_risk failed: {str(e)}")
            raise

    @staticmethod
    def update_risk(db: Session, risk_id: int, risk_update: schemas.RiskUpdate, updated_by_id: int = None) -> Optional[Risk]:
        try:
            db_risk = RiskService.get_risk(db, risk_id)
            if not db_risk:
                return None

            old_score = db_risk.risk_score
            old_level = db_risk.risk_level

            update_data = risk_update.model_dump(exclude_unset=True)

            for k, v in update_data.items():
                setattr(db_risk, k, v)

            if "probability" in update_data or "impact" in update_data:
                db_risk.risk_score = float(db_risk.probability) * float(db_risk.impact)
                db_risk.risk_level = RiskService._calculate_risk_level(db_risk.risk_score)

            db_risk.last_updated_by_id = updated_by_id
            db_risk.last_updated_at = datetime.utcnow()

            RiskService._commit(db)
            db.refresh(db_risk)

            RiskService._log_risk_change(
                db,
                risk_id,
                updated_by_id,
                old_score=old_score,
                new_score=db_risk.risk_score,
                old_level=old_level,
                new_level=db_risk.risk_level,
                reason="Risk updated",
            )

            return db_risk

        except Exception as e:
            logger.error(f"update_risk failed: {str(e)}")
            raise

    @staticmethod
    def delete_risk(db: Session, risk_id: int) -> bool:
        try:
            db_risk = RiskService.get_risk(db, risk_id)
            if not db_risk:
                return False

            db_risk.is_active = False
            db_risk.updated_at = datetime.utcnow()

            RiskService._commit(db)
            return True

        except Exception as e:
            logger.error(f"delete_risk failed: {str(e)}")
            return False

    # =========================
    # INCIDENT LINKING
    # =========================

    @staticmethod
    def link_incident_to_risk(db: Session, incident_id: int, risk_id: int,
                              relationship_type: str = "CAUSED_BY",
                              notes: str = None) -> Optional[IncidentRisk]:
        try:
            existing = db.query(IncidentRisk).filter_by(
                incident_id=incident_id,
                risk_id=risk_id
            ).first()

            if existing:
                return existing

            link = IncidentRisk(
                incident_id=incident_id,
                risk_id=risk_id,
                relationship_type=relationship_type,
                notes=notes,
                created_at=datetime.utcnow()
            )

            db.add(link)
            RiskService._commit(db)

            RiskService.recalculate_risk_from_incidents(db, risk_id)
            return link

        except Exception as e:
            logger.error(f"link_incident_to_risk failed: {str(e)}")
            return None

    @staticmethod
    def recalculate_risk_from_incidents(db: Session, risk_id: int) -> Optional[Risk]:
        try:
            risk = RiskService.get_risk(db, risk_id)
            if not risk:
                return None

            links = db.query(IncidentRisk).filter_by(risk_id=risk_id).all()
            incident_ids = [l.incident_id for l in links]

            if not incident_ids:
                return risk

            incidents = db.query(Incident).filter(Incident.id.in_(incident_ids)).all()

            severity_score = 0
            for i in incidents:
                severity_score += RiskService.INCIDENT_SEVERITY_WEIGHT.get(i.severity, 1)

            risk.incident_count = len(incident_ids)
            risk.confidence_level = min(0.95, 0.5 + len(incident_ids) * 0.05)

            if severity_score >= 10:
                risk.probability = min(5, risk.probability + 1)

            risk.risk_score = float(risk.probability) * float(risk.impact)
            risk.risk_level = RiskService._calculate_risk_level(risk.risk_score)

            RiskService._commit(db)
            db.refresh(risk)

            return risk

        except Exception as e:
            logger.error(f"recalculate_risk_from_incidents failed: {str(e)}")
            return None

    # =========================
    # MITIGATION
    # =========================

    @staticmethod
    def add_mitigation_action(db: Session, mitigation: schemas.RiskMitigationCreate) -> Optional[RiskMitigation]:
        try:
            obj = RiskMitigation(**mitigation.model_dump())
            db.add(obj)
            RiskService._commit(db)
            db.refresh(obj)
            return obj
        except Exception as e:
            logger.error(f"add_mitigation_action failed: {str(e)}")
            return None

    # =========================
    # SLA & MONITORING
    # =========================

    @staticmethod
    def check_sla_breaches(db: Session) -> List[Risk]:
        try:
            risks = db.query(Risk).filter(
                Risk.sla_due_date < datetime.utcnow().date(),
                Risk.monitoring_status.in_(["OPEN", "IN_PROGRESS"]),
                Risk.is_active == True
            ).all()

            for r in risks:
                r.sla_breached = True

            RiskService._commit(db)
            return risks

        except Exception as e:
            logger.error(f"check_sla_breaches failed: {str(e)}")
            return []

    # =========================
    # COMMENTS & HISTORY
    # =========================

    @staticmethod
    def _log_risk_change(db: Session, risk_id: int, user_id: int,
                         old_score=None, new_score=None,
                         old_level=None, new_level=None,
                         reason=None):
        try:
            history = RiskHistory(
                risk_id=risk_id,
                changed_by_id=user_id,
                old_risk_score=old_score,
                new_risk_score=new_score,
                old_risk_level=old_level,
                new_risk_level=new_level,
                change_reason=reason,
                changed_at=datetime.utcnow(),
            )
            db.add(history)
            RiskService._commit(db)
        except Exception as e:
            logger.error(f"risk history log failed: {str(e)}")

    # =========================
    # ANALYTICS (OPTIMIZED)
    # =========================

    @staticmethod
    def get_risk_heatmap(db: Session) -> Dict[str, list]:
        try:
            risks = db.query(Risk).filter(Risk.is_active == True).all()

            heatmap = defaultdict(list)

            for r in risks:
                key = f"{r.probability}_{r.impact}"
                heatmap[key].append({
                    "id": r.id,
                    "title": r.title,
                    "level": r.risk_level,
                    "score": r.risk_score,
                    "dept": r.department
                })

            return dict(heatmap)

        except Exception as e:
            logger.error(f"get_risk_heatmap failed: {str(e)}")
            return {}

    @staticmethod
    def get_risk_statistics(db: Session) -> Dict[str, Any]:
        try:
            total = db.query(func.count(Risk.id)).filter(Risk.is_active == True).scalar() or 0

            by_level = dict(
                db.query(Risk.risk_level, func.count(Risk.id))
                .filter(Risk.is_active == True)
                .group_by(Risk.risk_level)
                .all()
            )

            return {
                "total": total,
                "by_level": by_level,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"get_risk_statistics failed: {str(e)}")
            return {"total": 0, "by_level": {}}

    @staticmethod
    def get_top_risks(db: Session, limit: int = 10) -> List[Risk]:
        try:
            return db.query(Risk).filter(Risk.is_active == True).order_by(
                desc(Risk.risk_score)
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"get_top_risks failed: {str(e)}")
            return []