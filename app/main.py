# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import routes_auth, routes_user


def create_application() -> FastAPI:
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
