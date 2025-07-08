from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String(10), nullable=False)
    destination = Column(String(10), nullable=False)
    tier = Column(Integer, nullable=False, default=3)  # 1, 2, or 3
    scan_interval_hours = Column(Integer, nullable=False, default=6)
    is_active = Column(Boolean, default=True)
    
    # Round-trip specific fields
    route_type = Column(String(20), default="round_trip")  # "round_trip" only
    region = Column(String(50))  # "europe_proche", "europe_populaire", "long_courrier"
    min_stay_nights = Column(Integer, default=3)  # Minimum stay duration
    max_stay_nights = Column(Integer, default=30)  # Maximum stay duration
    
    # Departure timing constraints
    min_advance_booking_days = Column(Integer, default=30)  # 1 month minimum
    max_advance_booking_days = Column(Integer, default=270)  # 9 months maximum
    
    # Short stay patterns (weekday constraints)
    allow_mon_wed = Column(Boolean, default=True)  # Monday to Wednesday (3 days)
    allow_tue_fri = Column(Boolean, default=True)  # Tuesday to Friday (4 days)
    allow_wed_sun = Column(Boolean, default=True)  # Wednesday to Sunday (5 days)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_route_origin_destination', 'origin', 'destination'),
        Index('idx_route_tier', 'tier'),
        Index('idx_route_region', 'region'),
        Index('idx_route_type', 'route_type'),
    )
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="route")
    deals = relationship("Deal", back_populates="route")


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    airline = Column(String(100))
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR")
    departure_date = Column(DateTime(timezone=True))
    return_date = Column(DateTime(timezone=True), nullable=True)
    flight_number = Column(String(20))
    booking_class = Column(String(20))
    raw_data = Column(JSON)  # Store complete API response
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())
    response_time = Column(Float, nullable=True)  # API response time in seconds
    status = Column(String(20), default="success")  # 'success', 'error', 'timeout'
    
    # Indexes
    __table_args__ = (
        Index('idx_price_history_route_scanned', 'route_id', 'scanned_at'),
        Index('idx_price_history_price', 'price'),
    )
    
    # Relationships
    route = relationship("Route", back_populates="price_history")


class Deal(Base):
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    price_history_id = Column(Integer, ForeignKey("price_history.id"), nullable=False)
    
    # Deal details
    normal_price = Column(Float, nullable=False)
    deal_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=False)
    anomaly_score = Column(Float)  # ML anomaly detection score
    
    # Round-trip specific fields
    stay_duration_nights = Column(Integer)  # Calculated stay duration
    departure_day_of_week = Column(Integer)  # 1=Monday, 7=Sunday
    return_day_of_week = Column(Integer)
    advance_booking_days = Column(Integer)  # Days between booking and departure
    
    # Deal validation flags
    meets_stay_requirements = Column(Boolean, default=False)
    meets_timing_requirements = Column(Boolean, default=False)
    meets_advance_booking = Column(Boolean, default=False)
    is_valid_round_trip = Column(Boolean, default=False)  # All requirements met
    
    # Deal metadata
    is_error_fare = Column(Boolean, default=False)
    confidence_score = Column(Float)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_deals_active_expires', 'is_active', 'expires_at'),
        Index('idx_deals_discount', 'discount_percentage'),
        Index('idx_deals_valid_round_trip', 'is_valid_round_trip'),
        Index('idx_deals_stay_duration', 'stay_duration_nights'),
        Index('idx_deals_advance_booking', 'advance_booking_days'),
    )
    
    # Relationships
    route = relationship("Route", back_populates="deals")
    alerts = relationship("Alert", back_populates="deal")