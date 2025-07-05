from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String(50))  # "price_drop", "error_fare", "flash_sale"
    status = Column(String(20), default="pending")  # pending, sent, failed, clicked
    
    # Delivery
    sent_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    
    # Content
    subject = Column(String(255))
    preview_text = Column(String(500))
    
    # Tracking
    sendgrid_message_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    deal = relationship("Deal", back_populates="alerts")


class AlertPreference(Base):
    __tablename__ = "alert_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Price thresholds
    min_discount_percentage = Column(Float, default=30.0)
    max_price_europe = Column(Float, default=200.0)
    max_price_international = Column(Float, default=800.0)
    
    # Route preferences
    preferred_routes = Column(JSON, default=list)
    excluded_airlines = Column(JSON, default=list)
    
    # Timing preferences
    advance_days_min = Column(Integer, default=7)
    advance_days_max = Column(Integer, default=180)
    
    # Notification limits (by tier)
    max_alerts_per_week = Column(Integer, default=3)
    
    # Relationships
    user = relationship("User", back_populates="alert_preferences")