import numpy as np
from typing import List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from app.utils.logger import logger


class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = "models/anomaly_detector.pkl"
        self.scaler_path = "models/scaler.pkl"
        
        # Load existing model if available
        self._load_model()
    
    def detect_anomaly(
        self, 
        historical_prices: List[float], 
        current_price: float
    ) -> Tuple[bool, float]:
        """
        Detect if current price is anomalous compared to historical
        Returns: (is_anomaly, anomaly_score)
        """
        if len(historical_prices) < 10:
            # Fallback to simple statistical method
            return self._simple_anomaly_detection(historical_prices, current_price)
        
        # Prepare features
        features = self._extract_features(historical_prices, current_price)
        
        # Ensure model is trained
        if self.model is None:
            self._train_model(historical_prices)
        
        # Predict
        features_scaled = self.scaler.transform([features])
        prediction = self.model.predict(features_scaled)[0]
        score = self.model.score_samples(features_scaled)[0]
        
        # -1 means anomaly in IsolationForest
        is_anomaly = prediction == -1
        
        # Convert score to probability (0-1)
        anomaly_probability = 1 / (1 + np.exp(score))
        
        return is_anomaly, anomaly_probability
    
    def _extract_features(
        self, 
        historical_prices: List[float], 
        current_price: float
    ) -> List[float]:
        """Extract statistical features for ML model"""
        prices = np.array(historical_prices)
        
        features = [
            current_price,
            np.mean(prices),
            np.std(prices),
            np.percentile(prices, 25),
            np.percentile(prices, 50),
            np.percentile(prices, 75),
            np.min(prices),
            np.max(prices),
            (current_price - np.mean(prices)) / (np.std(prices) + 1e-6),  # Z-score
            current_price / np.mean(prices),  # Price ratio
            len(prices)  # Sample size
        ]
        
        return features
    
    def _simple_anomaly_detection(
        self, 
        historical_prices: List[float], 
        current_price: float
    ) -> Tuple[bool, float]:
        """Simple statistical anomaly detection"""
        if not historical_prices:
            return False, 0.0
            
        prices = np.array(historical_prices)
        mean = np.mean(prices)
        std = np.std(prices)
        
        if std == 0:
            return current_price < mean * 0.7, 0.5
        
        z_score = abs((current_price - mean) / std)
        
        # Price drop more than 2 standard deviations
        is_anomaly = current_price < mean and z_score > 2
        
        # Convert z-score to probability-like score
        score = min(z_score / 4, 1.0) if is_anomaly else 0.0
        
        return is_anomaly, score
    
    def _train_model(self, sample_prices: List[float]):
        """Train the anomaly detection model"""
        # Generate training data
        training_data = []
        
        # Create synthetic normal prices
        for _ in range(100):
            synthetic_prices = np.random.normal(
                np.mean(sample_prices), 
                np.std(sample_prices), 
                len(sample_prices)
            ).tolist()
            
            # Add some variations
            for price in synthetic_prices:
                features = self._extract_features(synthetic_prices, price)
                training_data.append(features)
        
        # Train model
        X = np.array(training_data)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_scaled)
        
        # Save model
        self._save_model()
        
        logger.info("Anomaly detection model trained")
    
    def _save_model(self):
        """Save model and scaler to disk"""
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
    
    def _load_model(self):
        """Load model and scaler from disk"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Anomaly detection model loaded")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")
                self.model = None