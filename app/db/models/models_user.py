# app/db/models/models_user.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, Text
from datetime import datetime, timedelta, timezone
from app.db.database import Base  # Updated import
from app.db.enums.enums_user import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    # Primary identification fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Personal information
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone_number = Column(String(20))
    profile_picture = Column(String(255))  # URL or path to profile picture

    # Access control fields
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)

    # Preferences
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")

    # Security and audit fields
    last_login = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def full_name(self) -> str:
        """Returns the user's full name or username if no name is set."""
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.username

    def update_last_login(self) -> None:
        """Update last login timestamp with UTC timezone."""
        self.last_login = datetime.now(timezone.utc)

    def is_password_reset_token_valid(self, token_expiry: datetime) -> bool:
        """
        Check if password reset token is valid and not expired.
        """
        if not token_expiry:
            return False
        return datetime.now(timezone.utc) < token_expiry

    def soft_delete(self) -> None:
        """Soft delete the user by updating status and setting deletion timestamp."""
        self.status = UserStatus.INACTIVE
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    @property
    def is_recently_active(self) -> bool:
        """Check if user was active in the last 30 days."""
        if not self.last_login:
            return False
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        return self.last_login > thirty_days_ago

    @property
    def account_age_days(self) -> int:
        """Calculate the age of the account in days."""
        if not self.created_at:
            return 0
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.days
