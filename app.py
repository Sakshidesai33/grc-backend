"""
🚀 SINGLE WORKING BACKEND - GRC System
Fast, Clean, Submission-Ready

Run: uvicorn app:app --reload
or: python app.py
"""

import os
import uuid
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt

# =========================
# CONFIGURATION
# =========================

SECRET_KEY = "CHANGE_ME_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DB_PATH = "grc_system.db"

# =========================
# SETUP
# =========================

os.makedirs("logs", exist_ok=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GRC System API",
    version="1.0.0",
    description="Governance, Risk, and Compliance Management System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# =========================
# DATABASE SETUP
# =========================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        role TEXT DEFAULT 'user',
        department TEXT,
        is_active INTEGER DEFAULT 1,
        last_login TEXT,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL,
        status TEXT NOT NULL,
        department TEXT,
        assigned_to_id TEXT,
        reported_by_id TEXT NOT NULL,
        incident_date TEXT,
        resolved_at TEXT,
        tags TEXT,
        attachments TEXT,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS risks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        probability INTEGER,
        impact INTEGER,
        risk_score INTEGER,
        risk_level TEXT,
        department TEXT,
        status TEXT,
        owner_id TEXT,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS compliance_policies (
        id TEXT PRIMARY KEY,
        policy_name TEXT NOT NULL,
        description TEXT,
        status TEXT,
        department TEXT,
        last_audit_date TEXT,
        next_audit_date TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# =========================
# MODELS
# =========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    department: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str
    status: str = "OPEN"
    department: Optional[str] = None
    assigned_to_id: Optional[str] = None

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    assigned_to_id: Optional[str] = None

class RiskCreate(BaseModel):
    title: str
    description: str
    probability: int
    impact: int
    department: Optional[str] = None
    status: str = "ACTIVE"

class ComplianceCreate(BaseModel):
    policy_name: str
    description: Optional[str] = None
    status: str = "PENDING"
    department: Optional[str] = None

# =========================
# SECURITY HELPERS
# =========================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": user[0],
            "email": user[1],
            "first_name": user[3],
            "last_name": user[4],
            "role": user[5],
            "department": user[6],
            "is_active": bool(user[7])
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =========================
# STARTUP
# =========================

@app.on_event("startup")
def startup():
    init_db()

# =========================
# ROOT ENDPOINTS
# =========================

@app.get("/")
def root():
    return {"message": "GRC System API", "status": "running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# =========================
# AUTH ENDPOINTS
# =========================

@app.post("/auth/register", response_model=dict)
def register(user: UserCreate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO users 
        (id, email, password_hash, first_name, last_name, role, department, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        user.email,
        hash_password(user.password),
        user.first_name,
        user.last_name,
        user.role,
        user.department,
        now,
        now
    ))
    
    conn.commit()
    conn.close()
    
    return {"message": "User created successfully", "user_id": user_id}

@app.post("/auth/login", response_model=Token)
def login(form_data: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.email,))
    user = cursor.fetchone()
    
    if not user or not verify_password(form_data.password, user[2]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                  (datetime.utcnow().isoformat(), user[0]))
    conn.commit()
    conn.close()
    
    token = create_token({"sub": user[1]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# =========================
# INCIDENT ENDPOINTS
# =========================

@app.post("/incidents")
def create_incident(incident: IncidentCreate, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    incident_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO incidents 
        (id, title, description, severity, status, department, assigned_to_id, 
         reported_by_id, incident_date, tags, attachments, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_id,
        incident.title,
        incident.description,
        incident.severity,
        incident.status,
        incident.department,
        incident.assigned_to_id,
        current_user["id"],
        now,
        json.dumps([]),
        json.dumps([]),
        now,
        now
    ))
    
    conn.commit()
    conn.close()
    
    return {"id": incident_id, "message": "Incident created successfully"}

@app.get("/incidents")
def get_incidents(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT i.*, u.first_name, u.last_name 
        FROM incidents i 
        LEFT JOIN users u ON i.assigned_to_id = u.id 
        ORDER BY i.created_at DESC
    """)
    
    incidents = []
    for row in cursor.fetchall():
        incidents.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "severity": row[3],
            "status": row[4],
            "department": row[5],
            "assigned_to_id": row[6],
            "reported_by_id": row[7],
            "incident_date": row[8],
            "resolved_at": row[9],
            "tags": json.loads(row[10]) if row[10] else [],
            "attachments": json.loads(row[11]) if row[11] else [],
            "created_at": row[12],
            "updated_at": row[13],
            "assignee_name": f"{row[15]} {row[16]}" if row[15] else None
        })
    
    conn.close()
    return incidents

@app.put("/incidents/{incident_id}")
def update_incident(incident_id: str, incident: IncidentUpdate, 
                   current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if incident exists
    cursor.execute("SELECT id FROM incidents WHERE id = ?", (incident_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Update incident
    update_data = incident.model_dump(exclude_unset=True)
    if not update_data:
        conn.close()
        raise HTTPException(status_code=400, detail="No data to update")
    
    set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
    values = list(update_data.values()) + [datetime.utcnow().isoformat(), incident_id]
    
    cursor.execute(f"UPDATE incidents SET {set_clause}, updated_at = ? WHERE id = ?", values)
    conn.commit()
    conn.close()
    
    return {"message": "Incident updated successfully"}

# =========================
# RISK ENDPOINTS
# =========================

@app.post("/risks")
def create_risk(risk: RiskCreate, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    risk_id = str(uuid.uuid4())
    risk_score = risk.probability * risk.impact
    
    # Calculate risk level
    if risk_score >= 16:
        risk_level = "CRITICAL"
    elif risk_score >= 12:
        risk_level = "HIGH"
    elif risk_score >= 6:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO risks 
        (id, title, description, probability, impact, risk_score, risk_level, 
         department, status, owner_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        risk_id,
        risk.title,
        risk.description,
        risk.probability,
        risk.impact,
        risk_score,
        risk_level,
        risk.department,
        risk.status,
        current_user["id"],
        now,
        now
    ))
    
    conn.commit()
    conn.close()
    
    return {"id": risk_id, "risk_score": risk_score, "risk_level": risk_level}

@app.get("/risks")
def get_risks(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM risks ORDER BY created_at DESC")
    
    risks = []
    for row in cursor.fetchall():
        risks.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "probability": row[3],
            "impact": row[4],
            "risk_score": row[5],
            "risk_level": row[6],
            "department": row[7],
            "status": row[8],
            "owner_id": row[9],
            "created_at": row[10],
            "updated_at": row[11]
        })
    
    conn.close()
    return risks

# =========================
# COMPLIANCE ENDPOINTS
# =========================

@app.post("/compliance")
def create_policy(policy: ComplianceCreate, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    policy_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO compliance_policies 
        (id, policy_name, description, status, department, next_audit_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        policy_id,
        policy.policy_name,
        policy.description,
        policy.status,
        policy.department,
        (datetime.utcnow() + timedelta(days=365)).isoformat(),  # Next audit in 1 year
        now,
        now
    ))
    
    conn.commit()
    conn.close()
    
    return {"id": policy_id, "message": "Policy created successfully"}

@app.get("/compliance")
def get_policies(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM compliance_policies ORDER BY created_at DESC")
    
    policies = []
    for row in cursor.fetchall():
        policies.append({
            "id": row[0],
            "policy_name": row[1],
            "description": row[2],
            "status": row[3],
            "department": row[4],
            "last_audit_date": row[5],
            "next_audit_date": row[6],
            "created_at": row[7],
            "updated_at": row[8]
        })
    
    conn.close()
    return policies

# =========================
# DASHBOARD ENDPOINTS
# =========================

@app.get("/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM incidents WHERE status IN ('OPEN', 'INVESTIGATING')")
    open_incidents = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM incidents")
    total_incidents = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM risks WHERE risk_level IN ('HIGH', 'CRITICAL')")
    high_risks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM risks")
    total_risks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM compliance_policies WHERE status = 'COMPLIANT'")
    compliant_policies = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM compliance_policies")
    total_policies = cursor.fetchone()[0]
    
    conn.close()
    
    compliance_score = (compliant_policies / total_policies * 100) if total_policies > 0 else 0
    
    return {
        "incidents": {
            "open": open_incidents,
            "total": total_incidents
        },
        "risks": {
            "high_priority": high_risks,
            "total": total_risks
        },
        "compliance": {
            "score": round(compliance_score, 2),
            "compliant": compliant_policies,
            "total": total_policies
        },
        "summary": {
            "health_score": round(
                (100 - open_incidents * 2 + 100 - high_risks * 5 + compliance_score) / 3, 2
            )
        }
    }

# =========================
# RUN DIRECTLY
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
