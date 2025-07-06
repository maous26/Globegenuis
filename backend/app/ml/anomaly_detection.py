# backend/app/ml/anomaly_detection.py
import numpy as np
from typing import List, Tuple, Optional, Dict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
import os
from datetime import datetime, timedelta
from app.utils.logger import logger


class EnhancedAnomalyDetector:
    """
    Enhanced anomaly detection system for flight prices using multiple ML techniques
    """
    
    def __init__(self):
        self.isolation_forest = None
        self.dbscan = None
        self.scaler = StandardScaler()
        self.model_path = "models/enhanced_anomaly_detector.pkl"
        self.scaler_path = "models/enhanced_scaler.pkl"
        
        # Thresholds for different types of anomalies
        self.thresholds = {
            'error_fare': 0.7,      # > 70% discount likely error fare
            'great_deal': 0.5,      # > 50% discount is a great deal
            'good_deal': 0.3,       # > 30% discount is a good deal
        }
        
        # Load existing models if available
        self._load_models()
    
    def detect_anomaly(
        self, 
        route_data: Dict,
        current_price: float,
        historical_prices: List[float],
        additional_context: Optional[Dict] = None
    ) -> Dict:
        """
        Enhanced anomaly detection with multiple signals
        
        Args:
            route_data: Route information (origin, destination, etc.)
            current_price: Current price to evaluate
            historical_prices: List of historical prices
            additional_context: Additional data like seasonality, day of week, etc.
            
        Returns:
            Dict with anomaly details including score, type, confidence
        """
        
        # If not enough historical data, use rule-based approach
        if len(historical_prices) < 10:
            return self._rule_based_detection(
                route_data, current_price, historical_prices
            )
        
        # Extract comprehensive features
        features = self._extract_advanced_features(
            route_data, current_price, historical_prices, additional_context
        )
        
        # Ensure models are trained
        if self.isolation_forest is None:
            self._train_models(historical_prices, route_data)
        
        # Get predictions from multiple models
        features_scaled = self.scaler.transform([features])
        
        # Isolation Forest score
        iso_score = self.isolation_forest.score_samples(features_scaled)[0]
        iso_prediction = self.isolation_forest.predict(features_scaled)[0]
        
        # Convert to probability (0-1)
        anomaly_probability = 1 / (1 + np.exp(iso_score))
        
        # Calculate price drop percentage
        avg_price = np.mean(historical_prices)
        price_drop_pct = ((avg_price - current_price) / avg_price) * 100
        
        # Determine anomaly type
        anomaly_type = self._classify_anomaly(price_drop_pct, anomaly_probability)
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(
            historical_prices, current_price, anomaly_probability
        )
        
        # Estimate savings
        median_price = np.median(historical_prices)
        potential_savings = max(0, median_price - current_price)
        
        return {
            'is_anomaly': iso_prediction == -1,
            'anomaly_score': float(anomaly_probability),
            'anomaly_type': anomaly_type,
            'confidence': float(confidence),
            'price_drop_percentage': float(price_drop_pct),
            'normal_price': float(avg_price),
            'median_price': float(median_price),
            'potential_savings': float(potential_savings),
            'recommendation': self._get_recommendation(anomaly_type, confidence),
            'analysis': self._generate_analysis(
                route_data, current_price, historical_prices, anomaly_type
            )
        }
    
    def _extract_advanced_features(
        self,
        route_data: Dict,
        current_price: float,
        historical_prices: List[float],
        context: Optional[Dict] = None
    ) -> List[float]:
        """Extract comprehensive features for ML models"""
        
        prices = np.array(historical_prices)
        
        # Basic statistical features
        features = [
            current_price,
            np.mean(prices),
            np.std(prices),
            np.median(prices),
            np.percentile(prices, 25),
            np.percentile(prices, 75),
            np.min(prices),
            np.max(prices),
            prices[-1] if len(prices) > 0 else current_price,  # Most recent price
        ]
        
        # Price ratios and differences
        mean_price = np.mean(prices)
        features.extend([
            current_price / mean_price if mean_price > 0 else 1,
            (mean_price - current_price) / mean_price if mean_price > 0 else 0,
            current_price / np.median(prices) if np.median(prices) > 0 else 1,
            (current_price - np.min(prices)) / (np.max(prices) - np.min(prices)) 
                if np.max(prices) > np.min(prices) else 0.5,
        ])
        
        # Trend features
        if len(prices) >= 3:
            recent_trend = np.polyfit(range(len(prices[-5:])), prices[-5:], 1)[0]
            features.append(recent_trend)
        else:
            features.append(0)
        
        # Volatility
        if len(prices) >= 2:
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) if len(returns) > 0 else 0
            features.append(volatility)
        else:
            features.append(0)
        
        # Route-specific features
        route_distance = self._estimate_route_distance(
            route_data.get('origin', ''), 
            route_data.get('destination', '')
        )
        features.append(route_distance)
        
        # Seasonality features (if context provided)
        if context:
            departure_date = context.get('departure_date')
            if departure_date:
                days_advance = (departure_date - datetime.now()).days
                features.extend([
                    days_advance,
                    departure_date.weekday(),  # Day of week
                    departure_date.month,      # Month
                ])
            else:
                features.extend([30, 3, 6])  # Default values
        else:
            features.extend([30, 3, 6])
        
        # Z-score
        z_score = (current_price - mean_price) / (np.std(prices) + 1e-6)
        features.append(z_score)
        
        return features
    
    def _train_models(self, sample_prices: List[float], route_data: Dict):
        """Train anomaly detection models"""
        
        # Generate synthetic training data
        training_data = self._generate_training_data(sample_prices, route_data)
        
        if len(training_data) < 50:
            logger.warning("Insufficient training data for ML models")
            return
        
        # Prepare features
        X = np.array(training_data)
        
        # Scale features
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            bootstrap=True
        )
        self.isolation_forest.fit(X_scaled)
        
        # Train DBSCAN for clustering
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.dbscan.fit(X_scaled)
        
        # Save models
        self._save_models()
        
        logger.info("Enhanced anomaly detection models trained successfully")
    
    def _generate_training_data(
        self, 
        sample_prices: List[float], 
        route_data: Dict
    ) -> List[List[float]]:
        """Generate synthetic training data for model training"""
        
        training_data = []
        mean_price = np.mean(sample_prices)
        std_price = np.std(sample_prices)
        
        # Generate normal prices
        for _ in range(200):
            # Normal variation
            synthetic_prices = np.random.normal(mean_price, std_price, 20)
            synthetic_prices = np.maximum(synthetic_prices, mean_price * 0.3)
            
            for i in range(len(synthetic_prices)):
                features = self._extract_advanced_features(
                    route_data,
                    synthetic_prices[i],
                    synthetic_prices,
                    None
                )
                training_data.append(features)
        
        # Generate anomalous prices (cheaper)
        for _ in range(50):
            # Anomalous prices (30-80% cheaper)
            discount = np.random.uniform(0.3, 0.8)
            anomaly_price = mean_price * (1 - discount)
            
            features = self._extract_advanced_features(
                route_data,
                anomaly_price,
                sample_prices,
                None
            )
            training_data.append(features)
        
        return training_data
    
    def _rule_based_detection(
        self,
        route_data: Dict,
        current_price: float,
        historical_prices: List[float]
    ) -> Dict:
        """Fallback rule-based detection when insufficient data"""
        
        if not historical_prices:
            # Use route-based estimates
            estimated_price = self._estimate_price_by_route(route_data)
            price_drop_pct = ((estimated_price - current_price) / estimated_price) * 100
        else:
            avg_price = np.mean(historical_prices)
            price_drop_pct = ((avg_price - current_price) / avg_price) * 100
        
        # Simple threshold-based classification
        if price_drop_pct >= 70:
            anomaly_type = 'error_fare'
            anomaly_score = 0.9
            confidence = 0.8
        elif price_drop_pct >= 50:
            anomaly_type = 'great_deal'
            anomaly_score = 0.7
            confidence = 0.7
        elif price_drop_pct >= 30:
            anomaly_type = 'good_deal'
            anomaly_score = 0.5
            confidence = 0.6
        else:
            anomaly_type = 'normal'
            anomaly_score = 0.2
            confidence = 0.5
        
        return {
            'is_anomaly': price_drop_pct >= 30,
            'anomaly_score': anomaly_score,
            'anomaly_type': anomaly_type,
            'confidence': confidence,
            'price_drop_percentage': price_drop_pct,
            'normal_price': historical_prices[0] if historical_prices else estimated_price,
            'median_price': np.median(historical_prices) if historical_prices else estimated_price,
            'potential_savings': max(0, (historical_prices[0] if historical_prices else estimated_price) - current_price),
            'recommendation': self._get_recommendation(anomaly_type, confidence),
            'analysis': f"Prix {price_drop_pct:.0f}% en dessous de la normale"
        }
    
    def _classify_anomaly(self, price_drop_pct: float, anomaly_score: float) -> str:
        """Classify the type of anomaly"""
        
        if price_drop_pct >= 70 and anomaly_score > 0.7:
            return 'error_fare'
        elif price_drop_pct >= 50 and anomaly_score > 0.5:
            return 'great_deal'
        elif price_drop_pct >= 30 and anomaly_score > 0.3:
            return 'good_deal'
        else:
            return 'normal'
    
    def _calculate_confidence(
        self,
        historical_prices: List[float],
        current_price: float,
        anomaly_score: float
    ) -> float:
        """Calculate confidence in the anomaly detection"""
        
        # Factors affecting confidence:
        # 1. Amount of historical data
        data_confidence = min(len(historical_prices) / 50, 1.0)
        
        # 2. Consistency of the anomaly
        prices = np.array(historical_prices)
        price_std = np.std(prices)
        price_mean = np.mean(prices)
        
        # How many standard deviations away is the current price?
        z_score = abs((current_price - price_mean) / (price_std + 1e-6))
        consistency_confidence = min(z_score / 3, 1.0)
        
        # 3. Anomaly score strength
        score_confidence = anomaly_score
        
        # Weighted average
        confidence = (
            0.3 * data_confidence +
            0.4 * consistency_confidence +
            0.3 * score_confidence
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def _get_recommendation(self, anomaly_type: str, confidence: float) -> str:
        """Get action recommendation based on anomaly type and confidence"""
        
        if anomaly_type == 'error_fare':
            if confidence > 0.8:
                return "🚨 RÉSERVEZ IMMÉDIATEMENT ! Erreur de prix probable."
            else:
                return "⚡ Excellente opportunité, vérifiez et réservez rapidement."
        elif anomaly_type == 'great_deal':
            if confidence > 0.7:
                return "🔥 Super deal ! Réservez dans les prochaines heures."
            else:
                return "💰 Très bon prix, mérite votre attention."
        elif anomaly_type == 'good_deal':
            return "✅ Bon prix, considérez cette offre."
        else:
            return "ℹ️ Prix dans la normale pour cette route."
    
    def _generate_analysis(
        self,
        route_data: Dict,
        current_price: float,
        historical_prices: List[float],
        anomaly_type: str
    ) -> str:
        """Generate human-readable analysis"""
        
        avg_price = np.mean(historical_prices) if historical_prices else 0
        min_price = np.min(historical_prices) if historical_prices else 0
        
        if anomaly_type == 'error_fare':
            return (
                f"Prix exceptionnel détecté ! {current_price}€ pour {route_data.get('origin')} → "
                f"{route_data.get('destination')} alors que le prix moyen est de {avg_price:.0f}€. "
                f"C'est probablement une erreur de tarification qui sera corrigée rapidement."
            )
        elif anomaly_type == 'great_deal':
            return (
                f"Excellente affaire sur {route_data.get('origin')} → {route_data.get('destination')} ! "
                f"Prix actuel {current_price}€ vs moyenne de {avg_price:.0f}€. "
                f"Plus bas prix observé : {min_price:.0f}€."
            )
        else:
            return (
                f"Prix intéressant pour {route_data.get('origin')} → {route_data.get('destination')}. "
                f"Actuellement à {current_price}€."
            )
    
    def _estimate_route_distance(self, origin: str, destination: str) -> float:
        """Estimate route distance category (1-5 scale)"""
        
        # Simplified distance estimation based on route type
        domestic_routes = ['NCE', 'MRS', 'TLS', 'BOD', 'LYS', 'NTE']
        european_routes = ['MAD', 'BCN', 'ROM', 'LON', 'BER', 'AMS']
        medium_haul = ['IST', 'CAI', 'TLV', 'CMN']
        long_haul = ['JFK', 'LAX', 'BKK', 'NRT', 'DXB', 'SYD']
        
        if origin in domestic_routes or destination in domestic_routes:
            return 1
        elif origin in european_routes or destination in european_routes:
            return 2
        elif origin in medium_haul or destination in medium_haul:
            return 3
        elif origin in long_haul or destination in long_haul:
            return 4
        else:
            return 2.5  # Default
    
    def _estimate_price_by_route(self, route_data: Dict) -> float:
        """Estimate normal price based on route characteristics"""
        
        distance = self._estimate_route_distance(
            route_data.get('origin', ''),
            route_data.get('destination', '')
        )
        
        # Base prices by distance category
        base_prices = {
            1: 150,   # Domestic
            2: 250,   # European
            2.5: 300, # Default
            3: 500,   # Medium-haul
            4: 800,   # Long-haul
        }
        
        return base_prices.get(distance, 300)
    
    def _save_models(self):
        """Save trained models to disk"""
        os.makedirs("models", exist_ok=True)
        
        if self.isolation_forest:
            joblib.dump(self.isolation_forest, self.model_path)
        if self.scaler:
            joblib.dump(self.scaler, self.scaler_path)
        
        logger.info("Models saved successfully")
    
    def _load_models(self):
        """Load models from disk if available"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.isolation_forest = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Enhanced anomaly detection models loaded")
            except Exception as e:
                logger.warning(f"Could not load models: {e}")
                self.isolation_forest = None