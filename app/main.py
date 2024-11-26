# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import routes_auth, routes_user
import os
from sqlalchemy import inspect

# Import database components
from app.db.session import engine
from app.db.base import Base
from app.db.models.models_user import User  # Import all models here


def init_db():
    """Initialize the database, create tables if they don't exist."""
    inspector = inspect(engine)

    # Create database directory if it doesn't exist
    db_path = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
    os.makedirs(db_path, exist_ok=True)

    # Create all tables if they don't exist
    if not inspector.has_table("users"):  # Check if users table exists
        Base.metadata.create_all(bind=engine)
        print("Database initialized: Tables created")
    else:
        print("Database exists: Tables already present")


def create_application() -> FastAPI:
    # Initialize database before creating the application
    init_db()

    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Set up CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(routes_auth.router, prefix=settings.API_V1_PREFIX)
    application.include_router(routes_user.router, prefix=settings.API_V1_PREFIX)

    @application.get("/")
    async def root():
        return {
            "message": "Welcome to FastAPI Auth System",
            "docs": "/docs",
            "redoc": "/redoc",
        }

    return application


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
