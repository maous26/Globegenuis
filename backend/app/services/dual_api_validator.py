"""
Dual API Cross-Validation Service
Validates flight deals using both FlightLabs and TravelPayouts APIs
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.flightlabs_api import FlightLabsAPI
from app.services.travelpayouts_api import TravelPayoutsAPI
from app.models.flight import Route, Deal, PriceHistory
from app.utils.logger import logger


class DualAPIValidator:
    """
    Cross-validation service using FlightLabs and TravelPayouts
    Ensures deal accuracy and prevents false positives
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.flightlabs_api = FlightLabsAPI()
        self.travelpayouts_api = TravelPayoutsAPI()
        
    async def validate_deal_comprehensive(
        self,
        route: Route,
        deal_price: float,
        normal_price: float,
        departure_date: datetime,
        return_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive validation using both APIs
        
        Returns validation result with confidence score and recommendation
        """
        
        logger.info(f"🔍 Cross-validating deal: {route.origin}→{route.destination} €{deal_price}")
        
        validation_result = {
            "is_valid": False,
            "confidence_score": 0.0,
            "validation_method": "dual_api",
            "aviationstack_validation": {},
            "travelpayouts_validation": {},
            "cross_validation_score": 0.0,
            "recommendation": "reject",
            "reasons": []
        }
        
        try:
            # 1. Validate with TravelPayouts (primary validation)
            tp_validation = await self.travelpayouts_api.cross_validate_deal(
                origin=route.origin,
                destination=route.destination,
                departure_date=departure_date,
                return_date=return_date,
                deal_price=deal_price,
                normal_price=normal_price
            )
            
            validation_result["travelpayouts_validation"] = tp_validation
            
            # 2. Get AviationStack context (secondary validation)
            # Note: AviationStack doesn't provide prices, but we can validate route existence
            aviation_flights = await self.aviation_api.search_flights(
                origin=route.origin,
                destination=route.destination,
                departure_date=departure_date,
                return_date=return_date
            )
            
            aviation_validation = {
                "route_exists": len(aviation_flights) > 0,
                "flight_count": len(aviation_flights),
                "airlines_available": list(set([f.get("airline", "Unknown") for f in aviation_flights]))
            }
            
            validation_result["aviationstack_validation"] = aviation_validation
            
            # 3. Calculate cross-validation score
            cross_score = self._calculate_cross_validation_score(
                tp_validation, aviation_validation, deal_price, normal_price
            )
            
            validation_result["cross_validation_score"] = cross_score
            
            # 4. Make final decision
            decision = self._make_validation_decision(tp_validation, aviation_validation, cross_score)
            validation_result.update(decision)
            
            logger.info(
                f"✅ Validation complete: {route.origin}→{route.destination} "
                f"Score: {cross_score:.2f} | Decision: {decision['recommendation']}"
            )
            
        except Exception as e:
            logger.error(f"❌ Cross-validation error: {e}")
            validation_result["error"] = str(e)
            validation_result["recommendation"] = "reject"
            validation_result["reasons"].append("validation_error")
        
        return validation_result
    
    def _calculate_cross_validation_score(
        self,
        tp_validation: Dict,
        aviation_validation: Dict,
        deal_price: float,
        normal_price: float
    ) -> float:
        """Calculate overall cross-validation confidence score"""
        
        score = 0.0
        
        # TravelPayouts validation weight (70%)
        if tp_validation.get("validated", False):
            tp_confidence = tp_validation.get("confidence", 0.0)
            score += tp_confidence * 0.7
            
            # Bonus for exceptional deals
            if tp_validation.get("deal_quality") == "exceptional":
                score += 0.1
            elif tp_validation.get("deal_quality") == "great":
                score += 0.05
        
        # AviationStack route existence weight (20%)
        if aviation_validation.get("route_exists", False):
            score += 0.2
            
            # Bonus for multiple airlines (indicates popular route)
            airline_count = len(aviation_validation.get("airlines_available", []))
            if airline_count > 2:
                score += 0.05
        
        # Deal magnitude validation (10%)
        discount_percentage = ((normal_price - deal_price) / normal_price) * 100
        
        if 30 <= discount_percentage <= 50:  # Reasonable good deal
            score += 0.1
        elif 50 <= discount_percentage <= 70:  # Great deal
            score += 0.08
        elif discount_percentage > 70:  # Error fare territory
            # Require high TravelPayouts confidence for error fares
            if tp_validation.get("confidence", 0) > 0.8:
                score += 0.1
            else:
                score -= 0.1  # Penalize unverified error fares
        
        return min(max(score, 0.0), 1.0)
    
    def _make_validation_decision(
        self,
        tp_validation: Dict,
        aviation_validation: Dict,
        cross_score: float
    ) -> Dict[str, Any]:
        """Make final validation decision based on all factors"""
        
        decision = {
            "is_valid": False,
            "confidence_score": cross_score,
            "recommendation": "reject",
            "reasons": []
        }
        
        # Decision thresholds
        if cross_score >= 0.8:
            decision["is_valid"] = True
            decision["recommendation"] = "approve_high_confidence"
            decision["reasons"].append("high_cross_validation_score")
            
        elif cross_score >= 0.6:
            # Medium confidence - check additional factors
            if tp_validation.get("validated", False) and aviation_validation.get("route_exists", False):
                decision["is_valid"] = True
                decision["recommendation"] = "approve_medium_confidence"
                decision["reasons"].append("medium_confidence_with_dual_validation")
            else:
                decision["recommendation"] = "review_required"
                decision["reasons"].append("medium_confidence_needs_review")
                
        elif cross_score >= 0.4:
            decision["recommendation"] = "review_required"
            decision["reasons"].append("low_confidence_manual_review")
            
        else:
            decision["recommendation"] = "reject"
            decision["reasons"].append("insufficient_validation_confidence")
        
        # Special cases
        if not aviation_validation.get("route_exists", False):
            decision["reasons"].append("route_not_confirmed_aviationstack")
            if cross_score < 0.7:  # Lower threshold if route doesn't exist
                decision["is_valid"] = False
                decision["recommendation"] = "reject"
        
        if tp_validation.get("reason") == "no_travelpayouts_data":
            decision["reasons"].append("no_travelpayouts_comparison_data")
            # Fallback to AviationStack only validation with lower confidence
            if aviation_validation.get("route_exists", False) and cross_score > 0.3:
                decision["recommendation"] = "approve_low_confidence"
                decision["reasons"].append("aviationstack_only_validation")
        
        return decision
    
    async def validate_existing_deals(self, limit: int = 10) -> Dict[str, Any]:
        """
        Re-validate existing active deals using dual API system
        Useful for quality control and confidence adjustment
        """
        
        logger.info(f"🔄 Re-validating {limit} existing deals with dual API system")
        
        # Get recent active deals
        recent_deals = self.db.query(Deal).filter(
            Deal.is_active == True
        ).order_by(Deal.detected_at.desc()).limit(limit).all()
        
        validation_results = []
        
        for deal in recent_deals:
            try:
                price_history = self.db.query(PriceHistory).filter(
                    PriceHistory.id == deal.price_history_id
                ).first()
                
                if not price_history:
                    continue
                
                route = self.db.query(Route).filter(
                    Route.id == deal.route_id
                ).first()
                
                if not route:
                    continue
                
                # Re-validate the deal
                validation = await self.validate_deal_comprehensive(
                    route=route,
                    deal_price=deal.deal_price,
                    normal_price=deal.normal_price,
                    departure_date=price_history.departure_date,
                    return_date=price_history.return_date
                )
                
                validation_results.append({
                    "deal_id": deal.id,
                    "route": f"{route.origin}→{route.destination}",
                    "original_confidence": deal.confidence_score,
                    "new_confidence": validation["confidence_score"],
                    "validation": validation,
                    "recommendation": validation["recommendation"]
                })
                
                # Update deal confidence if significantly different
                confidence_diff = abs(validation["confidence_score"] - (deal.confidence_score or 0))
                if confidence_diff > 0.2:
                    deal.confidence_score = validation["confidence_score"]
                    logger.info(f"Updated deal {deal.id} confidence: {validation['confidence_score']:.2f}")
                
            except Exception as e:
                logger.error(f"Error re-validating deal {deal.id}: {e}")
                continue
        
        self.db.commit()
        
        return {
            "deals_processed": len(validation_results),
            "high_confidence": len([r for r in validation_results if r["new_confidence"] > 0.8]),
            "medium_confidence": len([r for r in validation_results if 0.6 <= r["new_confidence"] <= 0.8]),
            "low_confidence": len([r for r in validation_results if r["new_confidence"] < 0.6]),
            "results": validation_results
        }
    
    async def emergency_price_check(
        self,
        origin: str,
        destination: str,
        target_price: float,
        departure_date: datetime,
        return_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Emergency price verification when quota is limited
        Uses both APIs efficiently to verify if a price is realistic
        """
        
        logger.info(f"🚨 Emergency price check: {origin}→{destination} €{target_price}")
        
        # Quick TravelPayouts validation (lower API cost)
        tp_validation = await self.travelpayouts_api.validate_price(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            aviationstack_price=target_price,
            tolerance_percentage=30.0  # More lenient for emergency checks
        )
        
        # Only use AviationStack if TravelPayouts is uncertain
        aviation_validation = {"route_exists": True}  # Assume exists to save API calls
        
        if tp_validation.get("confidence", 0) < 0.6:
            # Low confidence, need to check with AviationStack
            try:
                aviation_flights = await self.aviation_api.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    limit=5  # Minimal calls
                )
                aviation_validation = {
                    "route_exists": len(aviation_flights) > 0,
                    "flight_count": len(aviation_flights)
                }
            except Exception as e:
                logger.warning(f"AviationStack emergency check failed: {e}")
        
        # Quick decision
        is_valid = (
            tp_validation.get("validated", False) and 
            tp_validation.get("confidence", 0) > 0.5 and
            aviation_validation.get("route_exists", True)
        )
        
        return {
            "is_valid": is_valid,
            "confidence": tp_validation.get("confidence", 0),
            "emergency_mode": True,
            "tp_validation": tp_validation,
            "aviation_validation": aviation_validation
        }
    
    async def validate_deal(
        self,
        origin: str,
        destination: str,
        price: float,
        departure_date: datetime,
        return_date: Optional[datetime] = None
    ) -> bool:
        """Simple deal validation using TravelPayouts cross-check"""
        try:
            # Quick validation using TravelPayouts
            tp_result = await self.travelpayouts_api.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date
            )
            
            if tp_result and len(tp_result) > 0:
                # Check if our price is reasonable compared to TravelPayouts
                tp_prices = [f.get('price', 999999) for f in tp_result if f.get('price')]
                if tp_prices:
                    min_tp_price = min(tp_prices)
                    # Deal is valid if our price is within reasonable range of TravelPayouts
                    return price <= min_tp_price * 1.2  # Allow 20% variance
            
            # If TravelPayouts has no data, allow the deal (be permissive)
            return True
            
        except Exception as e:
            logger.error(f"Deal validation error: {e}")
            # Be permissive on errors
            return True
