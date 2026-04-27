"""
GRC Multi-User System - Production Ready Backend
Clean, scalable, secure FastAPI + SQLite implementation
"""

import os
import json
import uuid
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Generator

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr


# =========================
# CONFIGURATION
# =========================

SECRET_KEY = "grc-super-secret-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DB_PATH = os.getenv("DB_PATH", "grc_multi_user.db")

ROLE_HIERARCHY = {
    "admin": 6,
    "risk_officer": 5,
    "compliance_officer": 4,
    "analyst": 3,
    "auditor": 2,
    "user": 1,
}


# =========================
# LOGGING
# =========================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("GRC_SYSTEM")


# =========================
# APP INIT
# =========================

app = FastAPI(
    title="GRC Multi-User System",
    version="2.0.0",
    description="Production-ready GRC backend with roles, incidents, risks, compliance"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =========================
# DATABASE
# =========================

def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        assigned_to_id INTEGER,
        reported_by_id INTEGER NOT NULL,
        incident_date TEXT,
        resolved_at TEXT,
        tags TEXT,
        attachments TEXT,
        category TEXT,
        timeline TEXT,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS risks (
        id TEXT PRIMARY KEY,
        risk_title TEXT NOT NULL,
        description TEXT NOT NULL,
        probability INTEGER,
        impact INTEGER,
        risk_level TEXT,
        department TEXT,
        status TEXT,
        owner_id INTEGER,
        approver_id INTEGER,
        mitigation_owner_id INTEGER,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS compliance_policies (
        id TEXT PRIMARY KEY,
        policy_name TEXT NOT NULL,
        description TEXT,
        status TEXT,
        department TEXT,
        auditor_id INTEGER,
        last_audit_date TEXT,
        next_audit_due TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


# =========================
# SECURITY HELPERS
# =========================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# =========================
# AUTH DEPENDENCY
# =========================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: sqlite3.Connection = Depends(get_db)
) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user:
        raise credentials_exception

    return dict(user)


def require_role(required: str):
    def wrapper(user: Dict = Depends(get_current_user)):
        if ROLE_HIERARCHY.get(user["role"], 0) < ROLE_HIERARCHY[required]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return user
    return wrapper


# =========================
# PYDANTIC MODELS
# =========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str = "user"
    department: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str


class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str
    status: str = "open"
    department: Optional[str]
    category: Optional[str]
    assigned_to_id: Optional[int]
    reported_by_id: int
    incident_date: str


class RiskCreate(BaseModel):
    risk_title: str
    description: str
    probability: int
    impact: int
    risk_level: str
    department: Optional[str]
    status: str = "active"


class ComplianceCreate(BaseModel):
    policy_name: str
    description: str
    status: str
    department: Optional[str]


# =========================
# UTILS
# =========================

def now():
    return datetime.utcnow().isoformat()


def safe_json_load(value):
    try:
        return json.loads(value) if value else None
    except:
        return None


def log_audit_action(action: str, user_id: str, user_name: str, user_role: str,
                     incident_id: str = None, compliance_id: str = None,
                     gdpr_request_id: str = None, target_user_name: str = None):

    conn = sqlite3.connect('grc_multi_user.db')
    cursor = conn.cursor()

    log_id = str(uuid.uuid4())
    now_time = datetime.now().isoformat()

    try:
        cursor.execute("""
            INSERT INTO audit_logs (
                id, action, user_id, user_name, user_role,
                incident_id, compliance_id, gdpr_request_id,
                target_user_name, timestamp, success
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id, action, user_id, user_name, user_role,
            incident_id, compliance_id, gdpr_request_id,
            target_user_name, now_time, 1
        ))

        conn.commit()
    except Exception as e:
        print("Audit log error:", e)
    finally:
        conn.close()


# =========================
# STARTUP
# =========================

@app.on_event("startup")
def startup():
    init_db()


# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {"message": "GRC System API", "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}


# =========================
# AUTH
# =========================

@app.post("/api/register")
def register(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    existing = db.execute(
        "SELECT id FROM users WHERE email = ?", (user.email,)
    ).fetchone()

    if existing:
        raise HTTPException(400, "Email already registered")

    db.execute("""
        INSERT INTO users
        (email, password_hash, first_name, last_name, role, department, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.email,
        hash_password(user.password),
        user.first_name,
        user.last_name,
        user.role,
        user.department,
        now(),
        now()
    ))

    db.commit()
    return {"message": "User created successfully"}


@app.post("/api/token", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: sqlite3.Connection = Depends(get_db)
):
    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (form.username,)
    ).fetchone()

    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    token = create_token({"sub": user["email"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    db.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (now(), user["id"])
    )
    db.commit()

    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/me")
def me(user: Dict = Depends(get_current_user)):
    return user


# =========================
# INCIDENTS
# =========================

@app.post("/api/incidents")
def create_incident(
    incident: IncidentCreate,
    user: Dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    incident_id = str(uuid.uuid4())

    db.execute("""
        INSERT INTO incidents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_id,
        incident.title,
        incident.description,
        incident.severity,
        incident.status,
        incident.department,
        incident.assigned_to_id,
        incident.reported_by_id,
        incident.incident_date,
        None,
        json.dumps([]),
        json.dumps([]),
        incident.category,
        json.dumps([{"event": "created", "time": now()}]),
        now(),
        now()
    ))

    db.commit()
    return {"id": incident_id}


@app.get("/api/incidents")
def list_incidents(
    user: Dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    rows = db.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item["tags"] = safe_json_load(item["tags"])
        item["attachments"] = safe_json_load(item["attachments"])
        item["timeline"] = safe_json_load(item["timeline"])
        result.append(item)

    return result


# =========================
# RISKS
# =========================

@app.post("/api/risks")
def create_risk(
    risk: RiskCreate,
    user: Dict = Depends(require_role("risk_officer")),
    db: sqlite3.Connection = Depends(get_db)
):
    risk_id = str(uuid.uuid4())

    db.execute("""
        INSERT INTO risks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        risk_id,
        risk.risk_title,
        risk.description,
        risk.probability,
        risk.impact,
        risk.risk_level,
        risk.department,
        risk.status,
        None,
        None,
        None,
        now(),
        now()
    ))

    db.commit()
    return {"id": risk_id}


@app.get("/api/risks")
def list_risks(
    user: Dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    rows = db.execute("SELECT * FROM risks ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


# =========================
# COMPLIANCE
# =========================

@app.post("/api/compliance")
def create_policy(
    policy: ComplianceCreate,
    user: Dict = Depends(require_role("compliance_officer")),
    db: sqlite3.Connection = Depends(get_db)
):
    policy_id = str(uuid.uuid4())

    db.execute("""
        INSERT INTO compliance_policies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        policy_id,
        policy.policy_name,
        policy.description,
        policy.status,
        policy.department,
        None,
        None,
        None,
        now(),
        now()
    ))

    db.commit()
    return {"id": policy_id}


@app.get("/api/compliance")
def list_policies(
    user: Dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    rows = db.execute("SELECT * FROM compliance_policies ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


# =========================
# STARTUP CONFIGURATION
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_multi_user:app", host="0.0.0.0", port=8001, reload=True)