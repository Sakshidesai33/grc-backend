from .incidents import router as incidents_router
from .risks import router as risks_router
from .compliance import router as compliance_router
from .analytics import router as analytics_router
from .ai import router as ai_router

api_prefix = "/api/v1"

# Include all routers
routers = [
    incidents_router,
    risks_router,
    compliance_router,
    analytics_router,
    ai_router
]
