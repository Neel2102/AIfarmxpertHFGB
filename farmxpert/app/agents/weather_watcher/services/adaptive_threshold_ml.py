"""
Machine Learning Model for Adaptive Threshold Service
Uses historical data to learn optimal weather thresholds for different crops
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from datetime import datetime, timedelta
from loguru import logger

class AdaptiveThresholdMLModel:
    """
    Machine Learning model for adaptive weather thresholds
    Learns from historical data to optimize thresholds based on:
    - Crop type and growth stage
    - Location and climate patterns
    - Historical crop performance
    - Weather impact on crop health
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "adaptive_threshold_model.pkl"
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.models = {}  # Separate model for each threshold type
        self.feature_columns = []
        self.is_trained = False
        
        # Threshold types we predict
        self.threshold_types = [
            "heat_stress_temp",
            "heavy_rain_mm", 
            "high_wind_kmh",
            "low_temp_threshold",
            "drought_days_threshold"
        ]
        
        # Initialize models for each threshold
        for threshold_type in self.threshold_types:
            self.models[threshold_type] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
    
    def prepare_features(self, data: List[Dict]) -> pd.DataFrame:
        """
        Prepare features for ML training
        
        Features include:
        - Crop characteristics (type, growth stage, health)
        - Location data (latitude, climate zone)
        - Temporal features (season, month)
        - Weather history (recent patterns)
        - Crop performance metrics
        """
        features = []
        
        for record in data:
            feature_dict = {}
            
            # Crop features
            feature_dict['crop_name'] = record.get('crop_name', 'unknown')
            feature_dict['growth_stage'] = record.get('growth_stage', 'unknown')
            feature_dict['growth_health_status'] = record.get('growth_health_status', 'NORMAL')
            feature_dict['days_since_sowing'] = record.get('days_since_sowing', 0)
            feature_dict['crop_confidence'] = record.get('stage_confidence', 0.5)
            
            # Location features
            location = record.get('location', {})
            feature_dict['latitude'] = location.get('latitude', 0.0)
            feature_dict['longitude'] = location.get('longitude', 0.0)
            feature_dict['elevation'] = location.get('elevation', 0.0)
            feature_dict['climate_zone'] = location.get('climate_zone', 'tropical')
            
            # Temporal features
            date = record.get('date', datetime.now())
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            feature_dict['month'] = date.month
            feature_dict['season'] = self._get_season(date.month)
            feature_dict['day_of_year'] = date.timetuple().tm_yday
            
            # Weather history features
            weather_history = record.get('weather_history', {})
            feature_dict['avg_temp_7d'] = weather_history.get('avg_temp_7d', 25.0)
            feature_dict['avg_humidity_7d'] = weather_history.get('avg_humidity_7d', 60.0)
            feature_dict['total_rain_7d'] = weather_history.get('total_rain_7d', 0.0)
            feature_dict['max_wind_7d'] = weather_history.get('max_wind_7d', 10.0)
            feature_dict['temp_variance_7d'] = weather_history.get('temp_variance_7d', 5.0)
            
            # Crop performance features
            performance = record.get('crop_performance', {})
            feature_dict['yield_trend'] = performance.get('yield_trend', 0.0)
            feature_dict['stress_events_count'] = performance.get('stress_events_count', 0)
            feature_dict['recovery_rate'] = performance.get('recovery_rate', 1.0)
            
            # Alert history
            alert_history = record.get('alert_history', {})
            feature_dict['heat_stress_events'] = alert_history.get('heat_stress_events', 0)
            feature_dict['drought_events'] = alert_history.get('drought_events', 0)
            feature_dict['flood_events'] = alert_history.get('flood_events', 0)
            
            features.append(feature_dict)
        
        df = pd.DataFrame(features)
        return df
    
    def _get_season(self, month: int) -> str:
        """Get season from month"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def encode_categorical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Encode categorical features"""
        df_encoded = df.copy()
        categorical_columns = ['crop_name', 'growth_stage', 'growth_health_status', 'climate_zone', 'season']
        
        for col in categorical_columns:
            if col in df.columns:
                if fit:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    df_encoded[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    if col in self.label_encoders:
                        # Handle unseen categories
                        unique_values = set(df[col].astype(str))
                        known_values = set(self.label_encoders[col].classes_)
                        
                        # Map unknown values to -1
                        df_encoded[col] = df[col].astype(str).apply(
                            lambda x: self.label_encoders[col].transform([x])[0] 
                            if x in known_values else -1
                        )
        
        return df_encoded
    
    def train(self, training_data: List[Dict]) -> Dict[str, float]:
        """
        Train the ML model with historical data
        
        Args:
            training_data: List of historical records with features and optimal thresholds
            
        Returns:
            Training metrics
        """
        logger.info("🤖 Training Adaptive Threshold ML Model...")
        
        # Prepare features
        df = self.prepare_features(training_data)
        self.feature_columns = df.columns.tolist()
        
        # Encode categorical features
        df_encoded = self.encode_categorical_features(df, fit=True)
        
        # Scale features
        X = self.scaler.fit_transform(df_encoded)
        
        training_metrics = {}
        
        # Train separate model for each threshold type
        for threshold_type in self.threshold_types:
            # Extract target values
            y = np.array([record.get('optimal_thresholds', {}).get(threshold_type, 0.0) 
                          for record in training_data])
            
            # Skip if no target data
            if len(y) == 0 or np.all(y == 0):
                logger.warning(f"No target data for {threshold_type}, skipping...")
                continue
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.models[threshold_type].fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.models[threshold_type].predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            training_metrics[threshold_type] = {
                'mse': mse,
                'r2_score': r2,
                'samples': len(y_train)
            }
            
            logger.info(f"✅ {threshold_type}: R² = {r2:.3f}, MSE = {mse:.3f}")
        
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        logger.success("🎉 ML Model training completed!")
        return training_metrics
    
    def predict_thresholds(self, input_data: Dict) -> Dict[str, float]:
        """
        Predict optimal thresholds for given conditions
        
        Args:
            input_data: Dictionary with crop, location, and weather data
            
        Returns:
            Dictionary of predicted thresholds with confidence scores
        """
        if not self.is_trained:
            logger.warning("ML model not trained, using fallback")
            return self._fallback_thresholds(input_data)
        
        try:
            # Prepare features for prediction
            df = self.prepare_features([input_data])
            
            # Ensure all expected columns are present
            for col in self.feature_columns:
                if col not in df.columns:
                    df[col] = 0  # Default value for missing features
            
            # Encode and scale
            df_encoded = self.encode_categorical_features(df, fit=False)
            X = self.scaler.transform(df_encoded)
            
            predictions = {}
            confidences = {}
            
            # Predict each threshold
            for threshold_type in self.threshold_types:
                if threshold_type in self.models:
                    # Get prediction
                    pred = self.models[threshold_type].predict(X)[0]
                    
                    # Get prediction confidence (using tree variance)
                    tree_predictions = np.array([
                        tree.predict(X)[0] for tree in self.models[threshold_type].estimators_
                    ])
                    confidence = 1.0 - (np.std(tree_predictions) / np.mean(tree_predictions))
                    confidence = max(0.0, min(1.0, confidence))
                    
                    predictions[threshold_type] = float(pred)
                    confidences[threshold_type] = float(confidence)
            
            # Calculate overall confidence
            overall_confidence = np.mean(list(confidences.values()))
            
            logger.info(f"🤖 ML Prediction: {overall_confidence:.2f} confidence")
            
            return {
                'thresholds': predictions,
                'confidence': overall_confidence,
                'individual_confidences': confidences
            }
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._fallback_thresholds(input_data)
    
    def _fallback_thresholds(self, input_data: Dict) -> Dict[str, float]:
        """Fallback to rule-based thresholds when ML fails"""
        crop_name = input_data.get('crop_name', '').lower()
        health_status = input_data.get('growth_health_status', 'NORMAL')
        
        # Simple rule-based fallback
        if health_status in ['SLOW', 'ABNORMAL']:
            return {
                'thresholds': {
                    'heat_stress_temp': 34.0,
                    'heavy_rain_mm': 18.0,
                    'high_wind_kmh': 15.0
                },
                'confidence': 0.5
            }
        else:
            return {
                'thresholds': {
                    'heat_stress_temp': 37.0,
                    'heavy_rain_mm': 25.0,
                    'high_wind_kmh': 20.0
                },
                'confidence': 0.6
            }
    
    def save_model(self):
        """Save the trained model"""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'threshold_types': self.threshold_types,
            'is_trained': self.is_trained,
            'version': '1.0',
            'trained_at': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, self.model_path)
        logger.info(f"💾 Model saved to {self.model_path}")
    
    def load_model(self) -> bool:
        """Load a trained model"""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model file not found: {self.model_path}")
            return False
        
        try:
            model_data = joblib.load(self.model_path)
            
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_columns = model_data['feature_columns']
            self.threshold_types = model_data['threshold_types']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"✅ Model loaded from {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def generate_training_data(self, historical_data: List[Dict]) -> List[Dict]:
        """
        Generate training data from historical records
        This would typically come from your database or historical logs
        """
        training_data = []
        
        for record in historical_data:
            # Extract features
            features = {
                'crop_name': record.get('crop_name'),
                'growth_stage': record.get('growth_stage'),
                'growth_health_status': record.get('growth_health_status'),
                'days_since_sowing': record.get('days_since_sowing', 0),
                'stage_confidence': record.get('stage_confidence', 0.5),
                'location': record.get('location', {}),
                'date': record.get('date', datetime.now()),
                'weather_history': record.get('weather_history', {}),
                'crop_performance': record.get('crop_performance', {}),
                'alert_history': record.get('alert_history', {}),
                'optimal_thresholds': record.get('optimal_thresholds', {})
            }
            
            training_data.append(features)
        
        return training_data
