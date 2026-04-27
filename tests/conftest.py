"""
Test configuration and fixtures for backend testing (PRODUCTION-GRADE)

This conftest provides a clean, isolated, high-performance testing database
setup for FastAPI/SQLAlchemy applications with proper lifecycle management,
transaction rollback, and safe model loading.
"""

import pytest
import sys
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# ===========================
# PATH CONFIGURATION
# ===========================

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# ===========================
# TEST DATABASE CONFIG
# ===========================

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # required for SQLite + threading tests
    },
    poolclass=StaticPool,  # ensures same in-memory DB across connections
    future=True,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


# ===========================
# CORE FIXTURE
# ===========================

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Provides a fully isolated database session per test.

    Features:
    - Fresh schema per test
    - Transaction rollback after each test
    - Safe model import handling
    - Production-grade isolation
    """

    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        # Lazy import to avoid circular dependency issues
        try:
            from models import Base  # type: ignore
            Base.metadata.create_all(bind=connection)
        except Exception:
            # Models may not exist in some test contexts
            pass

        yield session

    finally:
        # CLEANUP (CRITICAL FOR TEST ISOLATION)
        session.close()
        transaction.rollback()
        connection.close()


# ===========================
# OPTIONAL FAST API OVERRIDE SUPPORT
# ===========================

@pytest.fixture(scope="function")
def override_get_db(db: Session):
    """
    Dependency override for FastAPI apps.
    Use this when testing API endpoints.
    """

    def _override():
        try:
            yield db
        finally:
            pass

    return _override


# ===========================
# PERFORMANCE TEST HELPERS
# ===========================

@pytest.fixture(scope="function")
def clean_db(db: Session):
    """
    Ensures absolutely clean DB state for strict tests.
    Useful for performance / concurrency / SRS validation tests.
    """
    try:
        yield db
    finally:
        # aggressive cleanup (safe for SQLite memory DB)
        db.rollback()


# ===========================
# TEST CONFIGURATION HOOKS
# ===========================

def pytest_configure(config):
    """
    Global pytest configuration hook.
    Enables consistent test environment setup.
    """
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running"
    )