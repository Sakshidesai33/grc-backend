from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from app_new.models.incident import Incident
from app_new.schemas.incident import IncidentCreate, IncidentUpdate, IncidentResponse
from app_new.core.deps import get_current_user
from app_new.models.user import User
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=IncidentResponse)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_incident = Incident(
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        department=incident.department,
        status=incident.status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    return db_incident

@router.get("/")
def get_incidents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        incidents = db.query(Incident).offset(skip).limit(limit).all()
        result = []
        for incident in incidents:
            result.append({
                "id": incident.id,
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity,
                "department": incident.department,
                "status": incident.status,
                "created_at": incident.created_at,
                "updated_at": incident.updated_at
            })
        return result
    except Exception as e:
        import traceback
        print(f"Error in get_incidents: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    incident_update: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Update fields
    update_data = incident_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)
    
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    return incident

@router.delete("/{incident_id}")
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    db.delete(incident)
    db.commit()
    
    return {"message": "Incident deleted successfully"}
