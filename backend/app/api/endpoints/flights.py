from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from app.api import deps
from app.models import Route, Deal
from app.schemas.flight import Route as RouteSchema, Deal as DealSchema
from app.services.flight_scanner import FlightScanner
from app.core.database import get_db

router = APIRouter()


@router.get("/routes", response_model=List[RouteSchema])
def get_routes(
    tier: Optional[int] = Query(None, ge=1, le=3),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all routes, optionally filtered by tier"""
    query = db.query(Route)
    
    if tier:
        query = query.filter(Route.tier == tier)
    
    routes = query.offset(skip).limit(limit).all()
    return routes


@router.get("/deals", response_model=List[DealSchema])
def get_active_deals(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    min_discount: Optional[float] = Query(None, ge=0, le=100),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_user)
):
    """Get active deals based on user preferences"""
    query = db.query(Deal).filter(Deal.is_active == True)
    
    # Filter by route if specified
    if origin or destination:
        query = query.join(Route)
        if origin:
            query = query.filter(Route.origin == origin.upper())
        if destination:
            query = query.filter(Route.destination == destination.upper())
    
    # Filter by minimum discount
    if min_discount:
        query = query.filter(Deal.discount_percentage >= min_discount)
    
    # Order by discount percentage
    deals = query.order_by(Deal.discount_percentage.desc())\
                 .offset(skip)\
                 .limit(limit)\
                 .all()
    
    return deals


@router.post("/scan/{route_id}")
async def scan_route(
    route_id: int = Path(..., description="ID of the route to scan"),
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_admin_user)
):
    """Manually trigger a scan for a specific route (admin only)"""
    route = db.query(Route).filter(Route.id == route_id).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    scanner = FlightScanner(db)
    deals = await scanner.scan_route(route)
    
    return {
        "route": f"{route.origin} -> {route.destination}",
        "deals_found": len(deals),
        "deals": [
            {
                "price": d.deal_price,
                "discount": f"{d.discount_percentage:.0f}%",
                "normal_price": d.normal_price
            }
            for d in deals
        ]
    }


@router.post("/scan/tier/{tier}")
async def scan_tier(
    tier: int = Path(..., ge=1, le=3, description="Tier level to scan"),
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_admin_user)
):
    """Manually trigger a scan for all routes in a tier (admin only)"""
    scanner = FlightScanner(db)
    result = await scanner.scan_all_routes(tier=tier)
    return result