# backend/app/models/api_tracking.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class ApiCall(Base):
    """Track individual API calls for monitoring"""
    __tablename__ = "api_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    api_provider = Column(String(50), nullable=False, default="aviationstack")  # flightlabs, travelpayouts, etc.
    endpoint = Column(String(255), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    called_at = Column(DateTime, default=datetime.utcnow, index=True)  # Renamed from timestamp
    response_time = Column(Float, nullable=True)  # in seconds
    success = Column(Boolean, default=True)  # success/failure flag
    status = Column(String(50), default="pending")  # pending, success, error
    error_message = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)  # Store JSON response data
    
    # Relationships
    route = relationship("Route", back_populates="api_calls")

class ApiQuotaUsage(Base):
    """Track daily API quota usage"""
    __tablename__ = "api_quota_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    calls_made = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Update the Route model to include the relationship
# In app/models/flight.py, add this to the Route class:
# api_calls = relationship("ApiCall", back_populates="route")