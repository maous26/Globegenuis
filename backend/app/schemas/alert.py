from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AlertPreferenceBase(BaseModel):
    min_discount_percentage: float = Field(default=30.0, ge=10.0, le=90.0)
    max_price_europe: float = Field(default=200.0, ge=50.0)
    max_price_international: float = Field(default=800.0, ge=100.0)
    preferred_routes: List[str] = []
    excluded_airlines: List[str] = []
    advance_days_min: int = Field(default=7, ge=1)
    advance_days_max: int = Field(default=180, le=365)


class AlertPreferenceCreate(AlertPreferenceBase):
    pass


class AlertPreferenceUpdate(AlertPreferenceBase):
    pass


class AlertPreference(AlertPreferenceBase):
    id: int
    user_id: int
    max_alerts_per_week: int
    
    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    alert_type: str
    subject: str
    preview_text: str


class AlertCreate(AlertBase):
    user_id: int
    deal_id: int


class Alert(AlertBase):
    id: int
    user_id: int
    deal_id: int
    status: str
    sent_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True