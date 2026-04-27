# auth.py (Production-Ready, Secure & Optimized)

from datetime import datetime, timedelta, timezone
from typing import Optional, Union

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
# 🔐 CONFIGURATION (SECURE)
# =========================

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_ONLY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if SECRET_KEY == "CHANGE_THIS_IN_PRODUCTION_ONLY":
    # Prevent silent insecure deployments
    print("WARNING: Using default SECRET_KEY. Set environment variable in production!")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


# =========================
# 🔒 PASSWORD UTILITIES
# =========================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against hashed password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash password securely using bcrypt."""
    return pwd_context.hash(password)


# =========================
# 👤 USER AUTHENTICATION
# =========================

def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate user using email and password.
    Returns user object if valid, else False.
    """
    try:
        user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            return False

        if not verify_password(password, user.password):
            return False

        return user

    except Exception:
        return False


# =========================
# 🎟️ JWT TOKEN HANDLING
# =========================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with expiration.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =========================
# 🔍 CURRENT USER DEPENDENCY
# =========================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
):
    """
    Decode JWT token and return current authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: Optional[str] = payload.get("sub")
        if not email:
            raise credentials_exception

        token_data = schemas.TokenData(email=email)

    except JWTError:
        raise credentials_exception

    try:
        user = db.query(models.User).filter(models.User.email == token_data.email).first()

        if not user:
            raise credentials_exception

        return user

    except Exception:
        raise credentials_exception


# =========================
# ✅ ACTIVE USER CHECK
# =========================

def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
):
    """
    Ensure user is active.
    """
    if not getattr(current_user, "is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user