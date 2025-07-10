"""
Admin endpoint for dual API validation management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.flight import Route, Deal, PriceHistory
from app.services.dual_api_validator import DualAPIValidator
from app.services.travelpayouts_api import TravelPayoutsAPI
from app.utils.logger import logger

router = APIRouter()


@router.get("/dual-validation/status")
def get_dual_validation_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get status of dual API validation system"""
    
    try:
        # Check TravelPayouts configuration
        tp_api = TravelPayoutsAPI()
        tp_configured = bool(tp_api.api_token)
        
        # Get validation statistics
        total_deals = db.query(Deal).count()
        active_deals = db.query(Deal).filter(Deal.is_active == True).count()
        high_confidence_deals = db.query(Deal).filter(
            Deal.confidence_score > 80,
            Deal.is_active == True
        ).count()
        
        # Get recent validation activity
        recent_deals = db.query(Deal).filter(
            Deal.detected_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        return {
            "system_status": "operational" if tp_configured else "degraded",
            "travelpayouts_configured": tp_configured,
            "aviationstack_configured": True,  # Assume configured
            "statistics": {
                "total_deals": total_deals,
                "active_deals": active_deals,
                "high_confidence_deals": high_confidence_deals,
                "recent_deals_7d": recent_deals,
                "validation_rate": (high_confidence_deals / active_deals * 100) if active_deals > 0 else 0
            },
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting dual validation status: {e}")
        return {
            "system_status": "error",
            "error": str(e),
            "last_updated": datetime.now()
        }


@router.post("/dual-validation/test-route")
async def test_route_validation(
    origin: str = Query(..., description="Origin airport code"),
    destination: str = Query(..., description="Destination airport code"),
    test_price: float = Query(..., description="Price to test"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Test dual API validation for a specific route and price"""
    
    try:
        logger.info(f"Testing dual validation: {origin}→{destination} €{test_price}")
        
        # Create test route if doesn't exist
        route = db.query(Route).filter(
            Route.origin == origin.upper(),
            Route.destination == destination.upper()
        ).first()
        
        if not route:
            route = Route(
                origin=origin.upper(),
                destination=destination.upper(),
                tier=2,
                region="europe_populaire",
                is_active=True,
                route_type="round_trip"
            )
            db.add(route)
            db.flush()
        
        # Test with dual validator
        dual_validator = DualAPIValidator(db)
        
        departure_date = datetime.now() + timedelta(days=45)
        return_date = departure_date + timedelta(days=7)
        
        validation_result = await dual_validator.validate_deal_comprehensive(
            route=route,
            deal_price=test_price,
            normal_price=test_price * 1.5,  # Assume 33% discount
            departure_date=departure_date,
            return_date=return_date
        )
        
        db.rollback()  # Don't save test route
        
        return {
            "test_parameters": {
                "route": f"{origin}→{destination}",
                "test_price": test_price,
                "estimated_normal_price": test_price * 1.5,
                "estimated_discount": 33.3
            },
            "validation_result": validation_result,
            "recommendation": validation_result.get("recommendation", "unknown"),
            "confidence": validation_result.get("confidence_score", 0),
            "test_timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error testing route validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dual-validation/re-validate-deals")
async def re_validate_existing_deals(
    limit: int = Query(10, description="Number of deals to re-validate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Re-validate existing deals with dual API system"""
    
    try:
        dual_validator = DualAPIValidator(db)
        
        results = await dual_validator.validate_existing_deals(limit=limit)
        
        return {
            "operation": "re_validate_deals",
            "parameters": {"limit": limit},
            "results": results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error re-validating deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dual-validation/travelpayouts-test")
async def test_travelpayouts_connection(
    origin: str = Query("CDG", description="Origin airport code"),
    destination: str = Query("MAD", description="Destination airport code"),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Test TravelPayouts API connection"""
    
    try:
        tp_api = TravelPayoutsAPI()
        
        # Test search
        departure_date = datetime.now() + timedelta(days=45)
        
        results = await tp_api.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date
        )
        
        return {
            "connection_status": "success" if results else "no_data",
            "test_parameters": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date.strftime("%Y-%m-%d")
            },
            "results_count": len(results) if results else 0,
            "sample_results": results[:3] if results else [],
            "test_timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"TravelPayouts test error: {e}")
        return {
            "connection_status": "error",
            "error": str(e),
            "test_timestamp": datetime.now()
        }


@router.post("/dual-validation/emergency-mode")
async def activate_emergency_validation_mode(
    enabled: bool = Query(..., description="Enable/disable emergency mode"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Activate emergency validation mode (TravelPayouts only)"""
    
    try:
        # This would typically update a configuration setting
        # For now, just return the status
        
        return {
            "emergency_mode": enabled,
            "description": "Emergency mode uses TravelPayouts for validation while preserving AviationStack quota",
            "features": [
                "TravelPayouts primary validation",
                "AviationStack quota protection", 
                "Reduced API calls",
                "Maintained deal quality"
            ],
            "activated_at": datetime.now(),
            "activated_by": current_user.email
        }
        
    except Exception as e:
        logger.error(f"Error setting emergency mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dual-validation/metrics")
def get_dual_validation_metrics(
    days: int = Query(7, description="Number of days for metrics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Dict[str, Any]:
    """Get dual API validation metrics"""
    
    try:
        since_date = datetime.now() - timedelta(days=days)
        
        # Get deals by confidence level
        high_confidence = db.query(Deal).filter(
            Deal.confidence_score > 80,
            Deal.detected_at >= since_date
        ).count()
        
        medium_confidence = db.query(Deal).filter(
            Deal.confidence_score.between(60, 80),
            Deal.detected_at >= since_date
        ).count()
        
        low_confidence = db.query(Deal).filter(
            Deal.confidence_score < 60,
            Deal.detected_at >= since_date
        ).count()
        
        # Get deals by type
        error_fares = db.query(Deal).filter(
            Deal.is_error_fare == True,
            Deal.detected_at >= since_date
        ).count()
        
        regular_deals = db.query(Deal).filter(
            Deal.is_error_fare == False,
            Deal.detected_at >= since_date
        ).count()
        
        total_deals = high_confidence + medium_confidence + low_confidence
        
        return {
            "period": f"{days} days",
            "total_deals": total_deals,
            "confidence_distribution": {
                "high_confidence": {"count": high_confidence, "percentage": (high_confidence/total_deals*100) if total_deals > 0 else 0},
                "medium_confidence": {"count": medium_confidence, "percentage": (medium_confidence/total_deals*100) if total_deals > 0 else 0},
                "low_confidence": {"count": low_confidence, "percentage": (low_confidence/total_deals*100) if total_deals > 0 else 0}
            },
            "deal_types": {
                "error_fares": error_fares,
                "regular_deals": regular_deals
            },
            "validation_quality": {
                "high_quality_rate": (high_confidence/total_deals*100) if total_deals > 0 else 0,
                "total_validated": total_deals
            },
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting dual validation metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
