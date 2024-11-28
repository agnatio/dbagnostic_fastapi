# app/routes/routes_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.db.models.models_user import User
from app.utils.utils_auth import (
    verify_password,
    create_access_token,
    get_password_hash,
)
from app.db.config import settings  # Import settings instead
from app.schemas.schemas_auth import Token, UserCreate, UserLogin
from app.db.enums.enums_user import UserStatus

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # Debug prints
    print(f"Login attempt with username/email: {form_data.username}")

    # Query debug
    user_query = db.query(User).filter(User.email == form_data.username)
    print(f"SQL Query: {user_query}")

    # Find user by email
    user = user_query.first()

    # Debug print user result
    print(f"User found: {user is not None}")
    if user:
        print(f"User email: {user.email}")

    if not user:
        # Let's check if any users exist in the database
        all_users = db.query(User).all()
        print(f"Total users in database: {len(all_users)}")
        if all_users:
            print("Existing user emails:")
            for u in all_users:
                print(f"- {u.email}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Debug print (remove in production)
    print(f"Attempting login for user: {user.email}")
    print(
        f"Password verification result: {verify_password(form_data.password, user.hashed_password)}"
    )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
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


@router.post("/test-auth", include_in_schema=False)
async def test_auth(form_data: OAuth2PasswordRequestForm = Depends()):
    """Temporary endpoint to test password handling"""
    return {
        "username": form_data.username,
        "password_length": len(form_data.password),
        "password_first_char": form_data.password[0] if form_data.password else None,
    }
