# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import routes_auth, routes_user
from sqlalchemy import inspect
import os

# Import new database components
from app.db.database import DatabaseFactory, verify_database, Base
from app.db.models.models_user import User  # Import all models here


def init_db():
    """Initialize the database, create tables if they don't exist."""
    db_factory = DatabaseFactory.get_instance()
    inspector = inspect(db_factory.engine)

    # Create database directory if it doesn't exist
    db_settings = db_factory.settings
    os.makedirs(db_settings.DB_DIR, exist_ok=True)

    # Create all tables if they don't exist
    if not inspector.has_table("users"):  # Check if users table exists
        Base.metadata.create_all(bind=db_factory.engine)
        print("Database initialized: Tables created")
    else:
        print("Database exists: Tables already present")


def create_application() -> FastAPI:
    # Verify database connection before creating the application
    if not verify_database():
        raise Exception("Database connection failed")

    # Initialize database
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
