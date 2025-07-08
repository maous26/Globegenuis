from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, users, flights, health, admin
from app.core.database import engine, Base
from app.utils.logger import logger

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url="/api/v1/openapi.json"
)

# Configure CORS with explicit methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Default React dev server
        "http://localhost:3001",  # Custom port React dev server  
        "http://localhost:3003",  # Custom port React dev server
        "http://localhost:3004",  # Alternate port React dev server
        "http://localhost:3005",  # Alternate port React dev server
        "http://127.0.0.1:3000",  # Alternative address
        "http://127.0.0.1:3001",  # Alternative address
        "http://127.0.0.1:3003",  # Alternative address
        "http://127.0.0.1:3004",  # Alternative address
        "http://127.0.0.1:3005",  # Alternative address
        "null",  # For file:// protocol requests
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["Content-Length"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(flights.router, prefix="/api/v1/flights", tags=["flights"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("Database connected")
    logger.info("Ready to scan for amazing flight deals! ✈️")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)