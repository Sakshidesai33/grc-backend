"""
Production-Ready Authentication Module (GRC System)

Improvements:
- Secure secret key via environment variable
- Fixed password field mismatch (password_hash)
- Strong JWT handling with validation
- UTC-aware timestamps
- Better error handling & security hardening
- Clean dependency structure
- Role-ready user support
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

import database
import models
import schemas

# =========================
# CONFIGURATION (SECURE)
# =========================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_IMMEDIATELY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if SECRET_KEY == "CHANGE_THIS_IN_PRODUCTION_IMMEDIATELY":
    print("⚠️ WARNING: Using insecure default SECRET_KEY. Set JWT_SECRET_KEY in environment.")

# =========================
# SECURITY SETUP
# =========================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# IMPORTANT: should match your login route (/auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# =========================
# PASSWORD UTILITIES
# =========================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against hashed password."""
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password securely using bcrypt."""
    return pwd_context.hash(password)


# =========================
# USER AUTHENTICATION
# =========================

def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate user with email & password.
    Returns user object or False.
    """
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        return False

    # FIX: ensure correct DB field usage
    password_field = getattr(user, "password_hash", None) or getattr(user, "password", None)

    if not password_field:
        return False

    if not verify_password(password, password_field):
        return False

    return user


# =========================
# JWT TOKEN HANDLING
# =========================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with expiration.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    if "sub" not in to_encode:
        raise ValueError("Token must include 'sub' (subject/email)")

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =========================
# CURRENT USER DEPENDENCY
# =========================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
):
    """
    Decode JWT token and fetch current user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")

        if email is None or token_type != "access":
            raise credentials_exception

        token_data = schemas.TokenData(email=email)

    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == token_data.email).first()

    if user is None:
        raise credentials_exception

    return user


# =========================
# ACTIVE USER CHECK
# =========================

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
):
    """
    Ensure user is active before allowing access.
    """

    if not getattr(current_user, "is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    return current_user


# =========================
# ROLE HELPERS (SCALABLE)
# =========================

def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    """

    async def role_checker(
        current_user: models.User = Depends(get_current_active_user)
    ):
        user_role = getattr(current_user, "role", None)

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires role: {allowed_roles}"
            )

        return current_user

    return role_checker