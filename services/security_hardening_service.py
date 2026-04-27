import asyncio
import hashlib
import secrets
import time
import json
import re
import logging
import os
import ssl
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import jwt
import redis

from fastapi import HTTPException

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# =========================
# Logging Setup (Safe Init)
# =========================
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/security.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("security_service")


# =========================
# Security Service
# =========================
class SecurityHardeningService:
    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        self.blocked_ips = set()

        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)

        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    # =========================
    # KEY MANAGEMENT
    # =========================
    def _generate_encryption_key(self) -> bytes:
        env_key = os.environ.get("ENCRYPTION_KEY")

        if env_key:
            salt = os.environ.get("ENCRYPTION_SALT", "default_salt").encode()

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=200000,
            )

            return base64.urlsafe_b64encode(kdf.derive(env_key.encode()))

        return Fernet.generate_key()

    # =========================
    # ENCRYPTION
    # =========================
    def encrypt_sensitive_data(self, data: str) -> str:
        try:
            return self.fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise HTTPException(status_code=500, detail="Encryption error")

    def decrypt_sensitive_data(self, data: str) -> str:
        try:
            return self.fernet.decrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise HTTPException(status_code=500, detail="Decryption error")

    # =========================
    # PASSWORD SECURITY
    # =========================
    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(32)

        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            200000,
        ).hex()

        return f"{salt}:{hashed}"

    def verify_password(self, password: str, stored: str) -> bool:
        try:
            salt, hashed = stored.split(":")

            new_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                200000,
            ).hex()

            return secrets.compare_digest(new_hash, hashed)

        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    # =========================
    # JWT AUTH
    # =========================
    def generate_token(self, user_id: str, expires: int = 3600) -> str:
        payload = {
            "user_id": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expires),
            "jti": secrets.token_urlsafe(32)
        }

        secret = os.environ.get("JWT_SECRET")
        if not secret:
            raise HTTPException(status_code=500, detail="JWT secret not configured")

        return jwt.encode(payload, secret, algorithm="HS256")

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            secret = os.environ.get("JWT_SECRET")
            return jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

    # =========================
    # RATE LIMITING
    # =========================
    async def check_rate_limit(self, ip: str, endpoint: str, limit: int = 100, window: int = 3600) -> bool:
        key = f"rl:{ip}:{endpoint}"

        try:
            current = self.redis_client.get(key)

            if current and int(current) >= limit:
                return False

            pipe = self.redis_client.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, window)
            pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return True

    # =========================
    # IP SECURITY
    # =========================
    async def block_ip(self, ip: str, reason: str, duration: int = 3600):
        self.blocked_ips.add(ip)

        data = {
            "ip": ip,
            "reason": reason,
            "time": datetime.utcnow().isoformat()
        }

        self.redis_client.setex(f"blocked:{ip}", duration, json.dumps(data))
        logger.warning(f"IP blocked: {ip} - {reason}")

    async def is_ip_blocked(self, ip: str) -> bool:
        return self.redis_client.exists(f"blocked:{ip}") == 1

    # =========================
    # INPUT VALIDATION (HARDENED)
    # =========================
    def validate_input(self, value: str, kind: str) -> bool:
        if not isinstance(value, str):
            return False

        patterns = {
            "email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
            "text": r"^[^<>]{1,500}$",
            "number": r"^-?\d+(\.\d+)?$"
        }

        if kind in patterns:
            return bool(re.match(patterns[kind], value))

        return True

    # =========================
    # SECURITY LOGGING
    # =========================
    def log_event(self, event: str, details: Dict[str, Any], ip: Optional[str] = None):
        conn = sqlite3.connect("grc_production.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO security_logs (id, event_type, timestamp, details, client_ip)
            VALUES (?, ?, ?, ?, ?)
        """, (
            secrets.token_urlsafe(32),
            event,
            datetime.utcnow().isoformat(),
            json.dumps(details),
            ip
        ))

        conn.commit()
        conn.close()

        logger.info(f"Security event: {event}")

    # =========================
    # SECURITY HEADERS
    # =========================
    def get_headers(self) -> Dict[str, str]:
        return self.security_headers.copy()

    # =========================
    # METRICS
    # =========================
    def get_metrics(self) -> Dict[str, Any]:
        conn = sqlite3.connect("grc_production.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT severity, COUNT(*) 
            FROM security_logs 
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY severity
        """)

        rows = cursor.fetchall()
        conn.close()

        return {
            "last_24h": {k: v for k, v in rows},
            "blocked_ips": len(self.blocked_ips),
            "timestamp": datetime.utcnow().isoformat()
        }


# =========================
# GLOBAL INSTANCE
# =========================
security_service = SecurityHardeningService()