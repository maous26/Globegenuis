# backend/app/tasks/flight_tasks.py
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.flight import Route, Deal
from app.models.user import User, UserTier
from app.models.alert import Alert
from app.services.flight_scanner import FlightScanner
from app.ml.anomaly_detection import EnhancedAnomalyDetector
from app.utils.logger import logger
import asyncio


@shared_task(name="app.tasks.flight_tasks.scan_tier_routes")
def scan_tier_routes(tier: int):
    """
    Scan all routes for a specific tier
    """
    logger.info(f"Starting scan for Tier {tier} routes")
    
    db = SessionLocal()
    scanner = FlightScanner(db)
    
    try:
        # Get active routes for this tier
        routes = db.query(Route).filter(
            and_(Route.tier == tier, Route.is_active == True)
        ).all()
        
        logger.info(f"Found {len(routes)} active routes for Tier {tier}")
        
        # Run async scanner
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            scanner.scan_all_routes(tier=tier)
        )
        
        logger.info(f"Tier {tier} scan complete: {result}")
        
        # Trigger alert processing if deals were found
        if result.get('deals_found', 0) > 0:
            process_new_deals.delay()
        
        return result
        
    except Exception as e:
        logger.error(f"Error scanning Tier {tier} routes: {e}")
        raise
    finally:
        db.close()
        

@shared_task(name="app.tasks.flight_tasks.scan_specific_route")
def scan_specific_route(route_id: int):
    """
    Scan a specific route on demand
    """
    logger.info(f"Scanning specific route ID: {route_id}")
    
    db = SessionLocal()
    scanner = FlightScanner(db)
    
    try:
        route = db.query(Route).filter(Route.id == route_id).first()
        
        if not route:
            logger.error(f"Route {route_id} not found")
            return {"error": "Route not found"}
        
        # Run async scanner
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        deals = loop.run_until_complete(scanner.scan_route(route))
        
        logger.info(f"Found {len(deals)} deals for route {route.origin}->{route.destination}")
        
        return {
            "route": f"{route.origin}->{route.destination}",
            "deals_found": len(deals),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error scanning route {route_id}: {e}")
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.flight_tasks.process_new_deals")
def process_new_deals():
    """
    Process newly detected deals and create alerts for users
    """
    logger.info("Processing new deals for user alerts")
    
    db = SessionLocal()
    
    try:
        # Get unprocessed deals from the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        new_deals = db.query(Deal).filter(
            and_(
                Deal.detected_at >= one_hour_ago,
                Deal.is_active == True,
                ~Deal.alerts.any()  # No alerts created yet
            )
        ).all()
        
        logger.info(f"Found {len(new_deals)} new deals to process")
        
        if not new_deals:
            return {"message": "No new deals to process"}
        
        # Get all active users with alert preferences
        active_users = db.query(User).filter(
            and_(
                User.is_active == True,
                User.email_notifications == True
            )
        ).all()
        
        alerts_created = 0
        
        for user in active_users:
            # Check user preferences
            if not user.alert_preferences:
                continue
                
            prefs = user.alert_preferences
            
            for deal in new_deals:
                # Check if deal matches user preferences
                if not _matches_user_preferences(user, deal, prefs):
                    continue
                
                # Check alert limits
                weekly_alerts = db.query(Alert).filter(
                    and_(
                        Alert.user_id == user.id,
                        Alert.created_at >= datetime.now() - timedelta(days=7)
                    )
                ).count()
                
                max_alerts = _get_max_alerts_for_tier(user.tier)
                if weekly_alerts >= max_alerts:
                    logger.info(f"User {user.email} reached weekly alert limit")
                    break
                
                # Create alert
                alert = Alert(
                    user_id=user.id,
                    deal_id=deal.id,
                    alert_type="price_drop" if not deal.is_error_fare else "error_fare",
                    status="pending",
                    subject=_generate_alert_subject(deal),
                    preview_text=_generate_alert_preview(deal)
                )
                db.add(alert)
                alerts_created += 1
        
        db.commit()
        logger.info(f"Created {alerts_created} alerts")
        
        # Trigger email sending
        if alerts_created > 0:
            send_pending_alerts.delay()
        
        return {
            "deals_processed": len(new_deals),
            "alerts_created": alerts_created,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error processing new deals: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.flight_tasks.clean_expired_deals")
def clean_expired_deals():
    """
    Deactivate expired deals
    """
    logger.info("Cleaning expired deals")
    
    db = SessionLocal()
    
    try:
        now = datetime.now()
        
        # Find expired deals
        expired_deals = db.query(Deal).filter(
            and_(
                Deal.expires_at < now,
                Deal.is_active == True
            )
        ).all()
        
        logger.info(f"Found {len(expired_deals)} expired deals")
        
        # Deactivate them
        for deal in expired_deals:
            deal.is_active = False
        
        db.commit()
        
        return {
            "deals_deactivated": len(expired_deals),
            "timestamp": now
        }
        
    except Exception as e:
        logger.error(f"Error cleaning expired deals: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.flight_tasks.analyze_route_performance")
def analyze_route_performance():
    """
    Analyze route performance and adjust scanning frequency
    """
    logger.info("Analyzing route performance")
    
    db = SessionLocal()
    
    try:
        # Get all routes with their deal statistics
        routes = db.query(Route).filter(Route.is_active == True).all()
        
        adjustments = []
        
        for route in routes:
            # Count deals in the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            deal_count = db.query(Deal).filter(
                and_(
                    Deal.route_id == route.id,
                    Deal.detected_at >= thirty_days_ago
                )
            ).count()
            
            # Adjust tier based on performance
            if deal_count > 20 and route.tier > 1:
                # High performing route, promote it
                route.tier = max(1, route.tier - 1)
                adjustments.append(f"Promoted {route.origin}->{route.destination} to Tier {route.tier}")
            elif deal_count < 5 and route.tier < 3:
                # Low performing route, demote it
                route.tier = min(3, route.tier + 1)
                adjustments.append(f"Demoted {route.origin}->{route.destination} to Tier {route.tier}")
            
            # Update scan interval
            route.scan_interval_hours = {1: 2, 2: 4, 3: 6}[route.tier]
        
        db.commit()
        
        logger.info(f"Route performance analysis complete: {len(adjustments)} adjustments made")
        
        return {
            "routes_analyzed": len(routes),
            "adjustments": adjustments,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing route performance: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Helper functions
def _matches_user_preferences(user: User, deal: Deal, prefs) -> bool:
    """Check if a deal matches user preferences"""
    
    # Check minimum discount
    if deal.discount_percentage < prefs.min_discount_percentage:
        return False
    
    # Check price limits
    route = deal.route
    is_european = route.destination in ['MAD', 'BCN', 'ROM', 'LON', 'BER', 'AMS', 'LIS', 'MXP']
    
    if is_european and deal.deal_price > prefs.max_price_europe:
        return False
    elif not is_european and deal.deal_price > prefs.max_price_international:
        return False
    
    # Check if route matches user preferences
    if user.home_airports and route.origin not in user.home_airports:
        return False
    
    if user.favorite_destinations:
        # At least show deals for favorite destinations
        if route.destination not in user.favorite_destinations:
            # But still show error fares
            if not deal.is_error_fare:
                return False
    
    return True


def _get_max_alerts_for_tier(tier: UserTier) -> int:
    """Get maximum alerts per week for user tier"""
    limits = {
        UserTier.FREE: 3,
        UserTier.ESSENTIAL: 10,
        UserTier.PREMIUM: 20,
        UserTier.PREMIUM_PLUS: 50
    }
    return limits.get(tier, 3)


def _generate_alert_subject(deal: Deal) -> str:
    """Generate email subject for alert"""
    route = deal.route
    
    if deal.is_error_fare:
        return f"🚨 ERREUR DE PRIX: {route.origin}→{route.destination} -{int(deal.discount_percentage)}% !"
    elif deal.discount_percentage >= 50:
        return f"⚡ Deal exceptionnel: -{int(deal.discount_percentage)}% sur {route.destination}"
    else:
        return f"✈️ Nouveau deal: {route.origin}→{route.destination} à {deal.deal_price}€"


def _generate_alert_preview(deal: Deal) -> str:
    """Generate preview text for alert"""
    savings = deal.normal_price - deal.deal_price
    return (
        f"Économisez {savings:.0f}€ sur votre vol {deal.route.origin}→{deal.route.destination}. "
        f"Prix actuel: {deal.deal_price}€ au lieu de {deal.normal_price}€"
    )


# backend/app/tasks/email_tasks.py
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.user import User
from app.models.flight import Deal
from app.services.email_service import EmailService
from app.utils.logger import logger


@shared_task(name="app.tasks.email_tasks.send_pending_alerts")
def send_pending_alerts():
    """
    Send all pending email alerts
    """
    logger.info("Sending pending email alerts")
    
    db = SessionLocal()
    email_service = EmailService()
    
    try:
        # Get pending alerts grouped by user
        pending_alerts = db.query(Alert).filter(
            Alert.status == "pending"
        ).all()
        
        if not pending_alerts:
            logger.info("No pending alerts to send")
            return {"message": "No pending alerts"}
        
        # Group alerts by user
        user_alerts = {}
        for alert in pending_alerts:
            user_id = alert.user_id
            if user_id not in user_alerts:
                user_alerts[user_id] = []
            user_alerts[user_id].append(alert)
        
        emails_sent = 0
        
        for user_id, alerts in user_alerts.items():
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.email_notifications:
                continue
            
            # Get deals for alerts
            deals = []
            for alert in alerts:
                deal = db.query(Deal).filter(Deal.id == alert.deal_id).first()
                if deal and deal.is_active:
                    deals.append(deal)
            
            if not deals:
                continue
            
            # Send email based on user preference
            if user.notification_frequency == "instant" or len(deals) >= 3:
                message_id = email_service.send_deal_alert(
                    user=user,
                    deals=deals,
                    alert_type="instant"
                )
                
                if message_id:
                    # Update alert status
                    for alert in alerts:
                        alert.status = "sent"
                        alert.sent_at = datetime.now()
                        alert.sendgrid_message_id = message_id
                    
                    emails_sent += 1
                    logger.info(f"Sent alert email to {user.email}")
                else:
                    logger.error(f"Failed to send email to {user.email}")
        
        db.commit()
        
        logger.info(f"Email sending complete: {emails_sent} emails sent")
        
        return {
            "emails_sent": emails_sent,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error sending pending alerts: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.email_tasks.send_daily_digest")
def send_daily_digest():
    """
    Send daily digest emails to users who prefer them
    """
    logger.info("Sending daily digest emails")
    
    db = SessionLocal()
    email_service = EmailService()
    
    try:
        # Get users with daily digest preference
        daily_users = db.query(User).filter(
            and_(
                User.is_active == True,
                User.email_notifications == True,
                User.notification_frequency == "daily"
            )
        ).all()
        
        logger.info(f"Found {len(daily_users)} users for daily digest")
        
        emails_sent = 0
        
        for user in daily_users:
            # Get deals from the last 24 hours matching user preferences
            yesterday = datetime.now() - timedelta(days=1)
            
            deals = db.query(Deal).join(Deal.route).filter(
                and_(
                    Deal.detected_at >= yesterday,
                    Deal.is_active == True,
                    Deal.discount_percentage >= (user.alert_preferences.min_discount_percentage 
                                               if user.alert_preferences else 30)
                )
            ).all()
            
            # Filter by user preferences
            filtered_deals = []
            for deal in deals:
                if user.home_airports and deal.route.origin in user.home_airports:
                    filtered_deals.append(deal)
                elif user.favorite_destinations and deal.route.destination in user.favorite_destinations:
                    filtered_deals.append(deal)
            
            if filtered_deals:
                message_id = email_service.send_deal_alert(
                    user=user,
                    deals=filtered_deals[:10],  # Limit to 10 best deals
                    alert_type="daily"
                )
                
                if message_id:
                    emails_sent += 1
                    logger.info(f"Sent daily digest to {user.email}")
        
        logger.info(f"Daily digest complete: {emails_sent} emails sent")
        
        return {
            "emails_sent": emails_sent,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error sending daily digest: {e}")
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.email_tasks.send_welcome_email")
def send_welcome_email(user_id: int):
    """
    Send welcome email to new user
    """
    logger.info(f"Sending welcome email to user {user_id}")
    
    db = SessionLocal()
    email_service = EmailService()
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.error(f"User {user_id} not found")
            return {"error": "User not found"}
        
        message_id = email_service.send_welcome_email(user)
        
        if message_id:
            logger.info(f"Welcome email sent to {user.email}")
            return {
                "email": user.email,
                "message_id": message_id,
                "timestamp": datetime.now()
            }
        else:
            logger.error(f"Failed to send welcome email to {user.email}")
            return {"error": "Failed to send email"}
            
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        raise
    finally:
        db.close()


@shared_task(name="app.tasks.email_tasks.process_pending_alerts")
def process_pending_alerts():
    """Main task to process and send all pending alerts"""
    logger.info("Processing pending alerts - main task")
    
    # First process new deals
    process_new_deals.delay()
    
    # Then send pending alerts
    send_pending_alerts.delay()
    
    return {
        "status": "Processing initiated",
        "timestamp": datetime.now()
    }