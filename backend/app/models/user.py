# backend/app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserTier(enum.Enum):
    FREE = "free"
    ESSENTIAL = "essential"
    PREMIUM = "premium"
    PREMIUM_PLUS = "premium_plus"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Subscription
    tier = Column(Enum(UserTier), default=UserTier.FREE)
    subscription_expires_at = Column(DateTime(timezone=True))
    
    # Preferences
    home_airports = Column(JSON, default=list)  # ["CDG", "ORY"]
    favorite_destinations = Column(JSON, default=list)
    travel_types = Column(JSON, default=list)  # ["leisure", "business", "family"]
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    notification_frequency = Column(String(20), default="instant")  # instant, daily, weekly
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=True)
    auth_provider = Column(String(50), default="email")  # "email" or "google"
    profile_picture = Column(String(500), nullable=True)
    
    # Admin roles
    is_admin = Column(Boolean, default=False)
    is_superadmin = Column(Boolean, default=False)
    admin_permissions = Column(JSON, default=list)  # ["routes", "users", "analytics"]
    
    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Onboarding progress
    onboarding_step = Column(Integer, default=1)
    onboarding_completed = Column(Boolean, default=False)
    
    # Progressive onboarding tracking
    first_alert_sent_at = Column(DateTime(timezone=True))
    alerts_opened_count = Column(Integer, default=0)
    personalization_completed_at = Column(DateTime(timezone=True))
    enrichment_completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    alerts = relationship("Alert", back_populates="user")
    alert_preferences = relationship("AlertPreference", back_populates="user", uselist=False)