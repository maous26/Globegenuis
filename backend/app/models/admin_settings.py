from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class AdminSettings(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    monitoring_email = Column(String, default="admin@globegenius.app")
    alert_notifications = Column(Boolean, default=True)
    daily_reports = Column(Boolean, default=True)
    api_quota_alerts = Column(Boolean, default=True)
    deal_alerts = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())