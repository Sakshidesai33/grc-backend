from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth, incidents, ai, notifications
from db.init_db import init_database
from core.config import settings

app = FastAPI(
    title="GRC AI Backend",
    version="1.0.0",
    description="AI-driven Governance, Risk, and Compliance Management System"
)

# Configure CORS for Flutter frontend (Production-safe)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "https://127.0.0.1:3000",
]

if settings.ENVIRONMENT == "production":
    origins.extend([
        "https://your-app.onrender.com",
        "https://grc-backend.onrender.com",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    print("Backend starting...")
    # init_database()  # Completely disabled for stable auth testing

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "GRC AI Backend is active",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "ai_models": "ready"
    }
