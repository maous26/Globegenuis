from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RouteBase(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    tier: int = Field(..., ge=1, le=3)


class RouteCreate(RouteBase):
    pass


class Route(RouteBase):
    id: int
    is_active: bool
    scan_interval_hours: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PricePoint(BaseModel):
    airline: str
    price: float
    currency: str = "EUR"
    departure_date: datetime
    return_date: Optional[datetime] = None
    flight_number: Optional[str] = None
    booking_class: Optional[str] = None


class DealBase(BaseModel):
    route_id: int
    normal_price: float
    deal_price: float
    discount_percentage: float
    anomaly_score: Optional[float] = None
    is_error_fare: bool = False
    confidence_score: Optional[float] = None
    expires_at: Optional[datetime] = None


class DealCreate(DealBase):
    price_history_id: int


class Deal(DealBase):
    id: int
    is_active: bool
    detected_at: datetime
    route: Route
    
    class Config:
        from_attributes = True


class DealAlert(Deal):
    """Deal formatted for alerts"""
    origin_city: str
    destination_city: str
    savings_amount: float
    example_dates: List[Dict[str, Any]]