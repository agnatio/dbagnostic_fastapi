# app/routes/routes_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy import inspect


from app.db.session import get_db
from app.db.models.models_user import User
from app.utils.utils_auth import (
    verify_password,
    create_access_token,
    get_password_hash,
)
from app.config import settings  # Import settings instead
from app.schemas.schemas_auth import Token, UserCreate, UserLogin
from app.db.enums.enums_user import UserStatus
from app.db.database import DatabaseFactory, Base

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # Try to find user by email or username
    user = (
        db.query(User)
        .filter(
            (User.email == form_data.username) | (User.username == form_data.username)
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or suspended",
        )

    # Create access token using settings
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Update last login
    user.update_last_login()
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        status=UserStatus.ACTIVE,  # You might want to change this based on your requirements
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


@router.post("/test-auth", include_in_schema=True)
async def test_auth(form_data: OAuth2PasswordRequestForm = Depends()):
    """Temporary endpoint to test password handling"""
    return {
        "username": form_data.username,
        "password_length": len(form_data.password),
        "password_first_char": form_data.password[0] if form_data.password else None,
    }


@router.get("/debug-tables", include_in_schema=True)
async def debug_tables():
    """Debug endpoint to check database tables"""
    factory = DatabaseFactory.get_instance()
    inspector = inspect(factory.engine)
    tables = inspector.get_table_names()

    table_details = {}
    for table in tables:
        columns = [
            {"name": col["name"], "type": str(col["type"])}
            for col in inspector.get_columns(table)
        ]
        table_details[table] = columns

    return {
        "tables": tables,
        "details": table_details,
        "metadata_tables": list(Base.metadata.tables.keys()),
    }
