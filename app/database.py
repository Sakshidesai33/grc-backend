"""
Enterprise Database Configuration
PostgreSQL with async support and connection pooling
"""

import os
import asyncpg
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://grc_user:grc_password@localhost/grc_db"
)

# SQLAlchemy setup
Base = declarative_base()
metadata = MetaData()

# Async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they're registered
            from app.models import user, incident, notification, compliance
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def close_db():
    """Close database connections"""
    await engine.dispose()

# Database models
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SECURITY_MANAGER = "security_manager"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    USER = "user"

class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationType(str, enum.Enum):
    INCIDENT = "incident"
    RISK = "risk"
    COMPLIANCE = "compliance"
    SYSTEM = "system"

class ComplianceStatus(str, enum.Enum):
    NOT_CHECKED = "not_checked"
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reported_incidents = relationship("Incident", back_populates="reporter", foreign_keys="Incident.reported_by")
    assigned_incidents = relationship("Incident", back_populates="assignee", foreign_keys="Incident.assigned_to")
    notifications = relationship("Notification", back_populates="user")

# Incident Model
class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(Enum(IncidentSeverity), nullable=False, index=True)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN, index=True)
    department = Column(String(100), nullable=False, index=True)
    
    # Foreign keys
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Additional fields
    system_affected = Column(String(255), nullable=True)
    impact_assessment = Column(JSON, nullable=True)
    root_cause_analysis = Column(JSON, nullable=True)
    ai_analysis = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    reporter = relationship("User", back_populates="reported_incidents", foreign_keys=[reported_by])
    assignee = relationship("User", back_populates="assigned_incidents", foreign_keys=[assigned_to])
    timeline = relationship("IncidentTimeline", back_populates="incident", cascade="all, delete-orphan")
    attachments = relationship("IncidentAttachment", back_populates="incident", cascade="all, delete-orphan")

# Incident Timeline Model
class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    action = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="timeline")
    user = relationship("User")

# Incident Attachment Model
class IncidentAttachment(Base):
    __tablename__ = "incident_attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="attachments")
    uploader = relationship("User")

# Notification Model
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    is_pinned = Column(Boolean, default=False)
    
    # Optional incident link
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    incident = relationship("Incident")

# Compliance Check Model
class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    
    # Status and scoring
    status = Column(Enum(ComplianceStatus), nullable=False, default=ComplianceStatus.NOT_CHECKED)
    score = Column(Integer, nullable=False, default=0)
    max_score = Column(Integer, nullable=False, default=100)
    
    # Audit information
    last_checked = Column(DateTime(timezone=True), nullable=True)
    next_check_due = Column(DateTime(timezone=True), nullable=True)
    checked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    checker = relationship("User")

# AI Analysis Model
class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # risk, classification, similarity, etc.
    
    # Analysis results
    results = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=False)
    model_version = Column(String(20), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident")

# System Configuration Model
class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
