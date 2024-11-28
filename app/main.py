# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import routes_auth, routes_user
from app.db.database import verify_database, init_database, Base, DatabaseFactory
from app.db.models.models_user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    try:
        print("Starting application initialization...")

        # Verify database connection
        if not verify_database():
            raise Exception("Database connection failed")
        print("Database connection verified successfully")

        # Initialize database and create tables
        print("Creating database tables...")
        db_factory = DatabaseFactory.get_instance()
        Base.metadata.create_all(bind=db_factory.engine)
        print("Database tables created successfully")

        # Include routers
        app.include_router(routes_auth.router, prefix=settings.API_V1_PREFIX)
        app.include_router(routes_user.router, prefix=settings.API_V1_PREFIX)
        print("Routers included successfully")

        yield
    finally:
        print("Shutting down application...")
        pass


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # Set up CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/")
    async def root():
        """
        Root endpoint providing API information and documentation links
        """
        return {
            "app_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_spec": f"{settings.API_V1_PREFIX}/openapi.json",
            },
            "api_prefix": settings.API_V1_PREFIX,
            "available_endpoints": [
                f"{settings.API_V1_PREFIX}/auth/login",
                f"{settings.API_V1_PREFIX}/auth/register",
                f"{settings.API_V1_PREFIX}/users/me",
            ],
            "status": "online",
            "cors_enabled": True,
        }

    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
