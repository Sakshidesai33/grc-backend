from fastapi import FastAPI
from api import auth, incidents, ai, notifications
from db.init_db import init_database

app = FastAPI(
    title="GRC AI Backend",
    version="1.0.0",
    description="AI-driven Governance, Risk, and Compliance Management System"
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
