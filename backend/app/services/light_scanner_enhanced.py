# backend/app/services/flight_scanner_enhanced.py
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.flight import Route, PriceHistory, Deal
from app.ml.anomaly_detection import EnhancedAnomalyDetector  # Version AVANCÉE !
from app.utils.logger import logger
from app.core.config import settings
import random


class EnhancedFlightScanner:
    """
    Scanner de vols avec détection ML avancée et intégration APIs réelles
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.anomaly_detector = EnhancedAnomalyDetector()
        self.flightlabs_key = settings.FLIGHTLABS_API_KEY if hasattr(settings, 'FLIGHTLABS_API_KEY') else None
        self.travelpayouts_token = settings.TRAVELPAYOUTS_TOKEN if hasattr(settings, 'TRAVELPAYOUTS_TOKEN') else None
        
    async def scan_route(self, route: Route) -> List[Deal]:
        """Scan une route avec détection ML avancée"""
        logger.info(f"🔍 Scanning route: {route.origin} → {route.destination}")
        
        deals_found = []
        
        # Dates à scanner (stratégie intelligente)
        scan_dates = self._get_strategic_scan_dates()
        
        for departure_date in scan_dates:
            try:
                # 1. Récupérer les prix depuis plusieurs sources
                prices_data = await self._fetch_prices_from_apis(
                    route.origin, 
                    route.destination, 
                    departure_date
                )
                
                if not prices_data:
                    continue
                
                # 2. Analyser chaque prix trouvé
                for price_info in prices_data:
                    # Stocker dans l'historique
                    price_history = PriceHistory(
                        route_id=route.id,
                        airline=price_info['airline'],
                        price=price_info['price'],
                        currency=price_info.get('currency', 'EUR'),
                        departure_date=departure_date,
                        flight_number=price_info.get('flight_number'),
                        booking_class=price_info.get('booking_class', 'economy'),
                        raw_data=price_info
                    )
                    self.db.add(price_history)
                    self.db.flush()
                    
                    # 3. Détection ML avancée
                    anomaly_result = await self._detect_anomaly_enhanced(
                        route, 
                        price_info['price'],
                        departure_date
                    )
                    
                    # 4. Créer un deal si anomalie détectée
                    if anomaly_result['is_anomaly'] and anomaly_result['price_drop_percentage'] >= 30:
                        deal = self._create_deal(
                            route, 
                            price_history, 
                            anomaly_result
                        )
                        if deal:
                            self.db.add(deal)
                            deals_found.append(deal)
                            
                            logger.info(
                                f"🎯 {anomaly_result['anomaly_type'].upper()} détecté! "
                                f"{route.origin}→{route.destination} "
                                f"€{price_info['price']} (-{anomaly_result['price_drop_percentage']:.0f}%) "
                                f"Confidence: {anomaly_result['confidence']*100:.0f}%"
                            )
                            
            except Exception as e:
                logger.error(f"Error scanning date {departure_date}: {e}")
                continue
        
        self.db.commit()
        logger.info(f"✅ Route scan complete: {len(deals_found)} deals found")
        return deals_found
    
    async def _fetch_prices_from_apis(
        self, 
        origin: str, 
        destination: str, 
        departure_date: datetime
    ) -> List[Dict[str, Any]]:
        """Récupérer les prix depuis plusieurs APIs"""
        all_prices = []
        
        # 1. FlightLabs API (si configurée)
        if self.flightlabs_key:
            flightlabs_prices = await self._fetch_flightlabs_prices(
                origin, destination, departure_date
            )
            all_prices.extend(flightlabs_prices)
        
        # 2. Travelpayouts API (si configurée)
        if self.travelpayouts_token:
            travelpayouts_prices = await self._fetch_travelpayouts_prices(
                origin, destination, departure_date
            )
            all_prices.extend(travelpayouts_prices)
        
        # 3. Si aucune API configurée, utiliser des données réalistes
        if not all_prices:
            logger.warning("No price APIs configured, using realistic simulation")
            all_prices = self._generate_realistic_prices(
                origin, destination, departure_date
            )
        
        return all_prices
    
    async def _fetch_flightlabs_prices(
        self, 
        origin: str, 
        destination: str, 
        departure_date: datetime
    ) -> List[Dict[str, Any]]:
        """Récupérer prix depuis FlightLabs"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://app.goflightlabs.com/search-best-flights",
                    params={
                        "access_key": self.flightlabs_key,
                        "adults": 1,
                        "origin": origin,
                        "destination": destination,
                        "departureDate": departure_date.strftime("%Y-%m-%d"),
                        "currency": "EUR"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_flightlabs_response(data)
                else:
                    logger.error(f"FlightLabs API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"FlightLabs fetch error: {e}")
            return []
    
    async def _fetch_travelpayouts_prices(
        self, 
        origin: str, 
        destination: str, 
        departure_date: datetime
    ) -> List[Dict[str, Any]]:
        """Récupérer prix depuis Travelpayouts"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.travelpayouts.com/aviasales/v3/prices_for_dates",
                    params={
                        "origin": origin,
                        "destination": destination,
                        "departure_at": departure_date.strftime("%Y-%m-%d"),
                        "currency": "eur",
                        "token": self.travelpayouts_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_travelpayouts_response(data)
                else:
                    logger.error(f"Travelpayouts API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Travelpayouts fetch error: {e}")
            return []
    
    def _parse_flightlabs_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parser la réponse FlightLabs"""
        prices = []
        
        if data.get("success") and data.get("data"):
            for flight in data["data"]:
                prices.append({
                    "airline": flight.get("airline", {}).get("name", "Unknown"),
                    "price": float(flight.get("price", {}).get("total", 0)),
                    "currency": flight.get("price", {}).get("currency", "EUR"),
                    "flight_number": flight.get("segments", [{}])[0].get("flightNumber"),
                    "booking_class": "economy",
                    "source": "flightlabs"
                })
        
        return prices
    
    def _parse_travelpayouts_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parser la réponse Travelpayouts"""
        prices = []
        
        if data.get("success") and data.get("data"):
            for price_data in data["data"]:
                prices.append({
                    "airline": price_data.get("airline", "Unknown"),
                    "price": float(price_data.get("price", 0)),
                    "currency": "EUR",
                    "flight_number": price_data.get("flight_number"),
                    "booking_class": price_data.get("trip_class", "economy"),
                    "source": "travelpayouts"
                })
        
        return prices
    
    async def _detect_anomaly_enhanced(
        self,
        route: Route,
        current_price: float,
        departure_date: datetime
    ) -> Dict[str, Any]:
        """Détection d'anomalie ML avancée"""
        
        # Récupérer l'historique des prix
        historical_prices = self.db.query(PriceHistory.price).filter(
            PriceHistory.route_id == route.id,
            PriceHistory.scanned_at >= datetime.now() - timedelta(days=90)
        ).order_by(PriceHistory.scanned_at.desc()).limit(100).all()
        
        prices_list = [p[0] for p in historical_prices] if historical_prices else []
        
        # Contexte additionnel pour le ML
        context = {
            'departure_date': departure_date,
            'days_advance': (departure_date - datetime.now()).days,
            'day_of_week': departure_date.weekday(),
            'month': departure_date.month,
            'is_weekend': departure_date.weekday() >= 5,
            'is_holiday_period': self._is_holiday_period(departure_date)
        }
        
        # Utiliser le détecteur ML avancé
        result = self.anomaly_detector.detect_anomaly(
            route_data={
                'origin': route.origin,
                'destination': route.destination,
                'tier': route.tier
            },
            current_price=current_price,
            historical_prices=prices_list,
            additional_context=context
        )
        
        return result
    
    def _create_deal(
        self, 
        route: Route, 
        price_history: PriceHistory, 
        anomaly_result: Dict
    ) -> Optional[Deal]:
        """Créer un deal basé sur les résultats de détection"""
        
        # Calculer l'expiration basée sur le type d'anomalie
        expiry_hours = {
            'error_fare': 6,      # Les erreurs de prix sont corrigées rapidement
            'great_deal': 24,     # Les super deals durent ~1 jour
            'good_deal': 48,      # Les bons deals peuvent durer plus longtemps
        }.get(anomaly_result['anomaly_type'], 24)
        
        deal = Deal(
            route_id=route.id,
            price_history_id=price_history.id,
            normal_price=anomaly_result['normal_price'],
            deal_price=price_history.price,
            discount_percentage=anomaly_result['price_drop_percentage'],
            anomaly_score=anomaly_result['anomaly_score'],
            is_error_fare=anomaly_result['anomaly_type'] == 'error_fare',
            confidence_score=anomaly_result['confidence'] * 100,
            expires_at=datetime.now() + timedelta(hours=expiry_hours),
            is_active=True
        )
        
        return deal
    
    def _get_strategic_scan_dates(self) -> List[datetime]:
        """Générer des dates de scan stratégiques"""
        dates = []
        now = datetime.now()
        
        # Court terme (7-30 jours) - Plus de granularité
        for days in [7, 10, 14, 21, 28]:
            dates.append(now + timedelta(days=days))
        
        # Moyen terme (1-3 mois) - Granularité moyenne
        for days in [45, 60, 75, 90]:
            dates.append(now + timedelta(days=days))
        
        # Long terme (3-6 mois) - Moins de granularité
        for days in [120, 150, 180]:
            dates.append(now + timedelta(days=days))
        
        return dates
    
    def _is_holiday_period(self, date: datetime) -> bool:
        """Vérifier si la date est en période de vacances"""
        # Périodes de vacances approximatives (France)
        holiday_periods = [
            (datetime(date.year, 7, 1), datetime(date.year, 8, 31)),  # Été
            (datetime(date.year, 12, 20), datetime(date.year + 1, 1, 5)),  # Noël
            (datetime(date.year, 2, 10), datetime(date.year, 3, 10)),  # Hiver
            (datetime(date.year, 4, 10), datetime(date.year, 5, 10)),  # Printemps
        ]
        
        for start, end in holiday_periods:
            if start <= date <= end:
                return True
        return False
    
    def _generate_realistic_prices(
        self, 
        origin: str, 
        destination: str, 
        departure_date: datetime
    ) -> List[Dict[str, Any]]:
        """Générer des prix réalistes pour le développement"""
        
        # Prix de base réalistes par type de route
        base_prices = {
            # Domestique France
            ("CDG", "NCE"): 120, ("CDG", "MRS"): 110, ("CDG", "TLS"): 100,
            ("CDG", "BOD"): 90, ("CDG", "LYS"): 80, ("CDG", "NTE"): 85,
            
            # Europe
            ("CDG", "MAD"): 180, ("CDG", "BCN"): 160, ("CDG", "FCO"): 170,
            ("CDG", "LHR"): 200, ("CDG", "AMS"): 150, ("CDG", "BER"): 180,
            ("CDG", "LIS"): 190, ("CDG", "DUB"): 170, ("CDG", "ATH"): 250,
            
            # Moyen-courrier
            ("CDG", "IST"): 350, ("CDG", "CAI"): 400, ("CDG", "TLV"): 450,
            ("CDG", "CMN"): 280, ("CDG", "TUN"): 320, ("CDG", "ALG"): 350,
            
            # Long-courrier
            ("CDG", "JFK"): 650, ("CDG", "LAX"): 750, ("CDG", "MIA"): 700,
            ("CDG", "NRT"): 900, ("CDG", "BKK"): 850, ("CDG", "SIN"): 950,
            ("CDG", "DXB"): 550, ("CDG", "DOH"): 600, ("CDG", "HKG"): 880,
        }
        
        key = (origin, destination)
        base_price = base_prices.get(key, 300)  # Prix par défaut
        
        # Facteurs de variation
        days_advance = (departure_date - datetime.now()).days
        
        # Facteur jour de la semaine (weekend plus cher)
        weekday_factor = 1.15 if departure_date.weekday() >= 5 else 1.0
        
        # Facteur avance (plus c'est loin, moins c'est cher jusqu'à un certain point)
        if days_advance < 7:
            advance_factor = 1.5
        elif days_advance < 14:
            advance_factor = 1.3
        elif days_advance < 30:
            advance_factor = 1.1
        elif days_advance < 60:
            advance_factor = 0.95
        else:
            advance_factor = 1.0
        
        # Facteur saisonnier
        season_factor = 1.3 if self._is_holiday_period(departure_date) else 1.0
        
        # Générer plusieurs prix avec variations
        airlines = [
            ("Air France", 1.0),
            ("Ryanair", 0.7),
            ("EasyJet", 0.75),
            ("Vueling", 0.8),
            ("Lufthansa", 1.1),
            ("KLM", 1.05)
        ]
        
        prices = []
        for airline, airline_factor in airlines:
            # Prix normal
            normal_price = base_price * weekday_factor * advance_factor * season_factor * airline_factor
            
            # Parfois créer une anomalie (10% de chance)
            if random.random() < 0.1:
                # Type d'anomalie aléatoire
                anomaly_type = random.choice(['error_fare', 'great_deal', 'good_deal'])
                discount = {
                    'error_fare': random.uniform(0.2, 0.3),    # 70-80% de réduction
                    'great_deal': random.uniform(0.4, 0.5),    # 50-60% de réduction
                    'good_deal': random.uniform(0.6, 0.7)      # 30-40% de réduction
                }[anomaly_type]
                
                price = normal_price * discount
                logger.info(f"🎲 Generated {anomaly_type}: {airline} {origin}→{destination} €{price:.0f}")
            else:
                # Variation normale ±15%
                price = normal_price * random.uniform(0.85, 1.15)
            
            prices.append({
                "airline": airline,
                "price": round(price, 2),
                "currency": "EUR",
                "flight_number": f"{airline[:2].upper()}{random.randint(100, 999)}",
                "booking_class": "economy",
                "source": "simulation"
            })
        
        return prices
    
    async def scan_all_routes(self, tier: Optional[int] = None) -> Dict[str, Any]:
        """Scanner toutes les routes ou un tier spécifique"""
        query = self.db.query(Route).filter(Route.is_active == True)
        
        if tier:
            query = query.filter(Route.tier == tier)
        
        routes = query.all()
        logger.info(f"📡 Scanning {len(routes)} routes (Tier {tier or 'ALL'})")
        
        total_deals = []
        total_errors = 0
        
        for i, route in enumerate(routes, 1):
            try:
                logger.info(f"Progress: {i}/{len(routes)} routes")
                deals = await self.scan_route(route)
                total_deals.extend(deals)
                
                # Petite pause pour éviter le rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scanning route {route.origin}→{route.destination}: {e}")
                total_errors += 1
                continue
        
        return {
            "routes_scanned": len(routes),
            "deals_found": len(total_deals),
            "errors": total_errors,
            "timestamp": datetime.now(),
            "deal_types": {
                "error_fares": sum(1 for d in total_deals if d.is_error_fare),
                "great_deals": sum(1 for d in total_deals if 50 <= d.discount_percentage < 70),
                "good_deals": sum(1 for d in total_deals if 30 <= d.discount_percentage < 50)
            }
        }