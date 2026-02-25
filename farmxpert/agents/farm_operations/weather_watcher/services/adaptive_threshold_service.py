from loguru import logger
from typing import Dict, Optional
from datetime import datetime
from .adaptive_threshold_ml import AdaptiveThresholdMLModel


class AdaptiveThresholdResult:
    def __init__(self, thresholds: Dict[str, float], confidence: float, source: str):
        self.thresholds = thresholds
        self.confidence = confidence
        self.source = source


class AdaptiveThresholdService:
    """
    ML-powered adaptive threshold tuner.
    Uses machine learning to optimize weather thresholds based on:
    - Crop type and growth stage
    - Historical performance data
    - Location-specific patterns
    - Real-time crop health status
    """

    # ---------------- SAFETY ---------------- #
    HARD_LIMITS = {
        "heat_stress_temp": (32.0, 40.0),
        "heavy_rain_mm": (10.0, 50.0),
        "high_wind_kmh": (10.0, 30.0),
        "low_temp_threshold": (5.0, 15.0),
        "drought_days_threshold": (3.0, 15.0)
    }

    MIN_ML_CONFIDENCE = 0.7
    MIN_STAGE_CONFIDENCE = 0.6
    
    # Initialize ML model
    ml_model = None

    @classmethod
    def initialize_ml_model(cls, model_path: str = None):
        """Initialize the ML model"""
        try:
            cls.ml_model = AdaptiveThresholdMLModel(model_path)
            if not cls.ml_model.load_model():
                logger.info("🤖 No pre-trained model found, will use fallback logic")
                cls.ml_model = None
            else:
                logger.success("✅ ML model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {e}")
            cls.ml_model = None

    # ---------------- PUBLIC API ---------------- #

    @classmethod
    def get_adjusted_thresholds(
        cls,
        crop_name: str,
        growth_stage: Optional[str],
        stage_confidence: float,
        growth_health_status: str,
        growth_alert_types: list[str],
        location_id: str,
        base_thresholds: Dict[str, float],
        location_data: Optional[Dict] = None,
        weather_history: Optional[Dict] = None,
        crop_performance: Optional[Dict] = None
    ) -> AdaptiveThresholdResult:

        logger.info(
            f"🌦️ AdaptiveThresholds | crop={crop_name}, "
            f"stage={growth_stage}, health={growth_health_status}"
        )

        # Initialize ML model if not already done
        if cls.ml_model is None:
            cls.initialize_ml_model()

        # ---- Stage confidence gate ----
        if not growth_stage or stage_confidence < cls.MIN_STAGE_CONFIDENCE:
            return AdaptiveThresholdResult(
                thresholds=base_thresholds,
                confidence=0.0,
                source="BASE_LOW_STAGE_CONF"
            )

        # ---- Try ML model ----
        if cls.ml_model and cls.ml_model.is_trained:
            ml_input = {
                'crop_name': crop_name,
                'growth_stage': growth_stage,
                'growth_health_status': growth_health_status,
                'stage_confidence': stage_confidence,
                'growth_alert_types': growth_alert_types,
                'location_id': location_id,
                'location': location_data or {},
                'weather_history': weather_history or {},
                'crop_performance': crop_performance or {},
                'date': datetime.now()
            }
            
            ml_output = cls.ml_model.predict_thresholds(ml_input)
            
            if ml_output['confidence'] >= cls.MIN_ML_CONFIDENCE:
                adjusted = cls._apply_safety_limits(
                    base_thresholds,
                    ml_output['thresholds']
                )
                
                logger.success(f"✅ ML thresholds applied (confidence: {ml_output['confidence']:.2f})")
                
                return AdaptiveThresholdResult(
                    thresholds=adjusted,
                    confidence=ml_output['confidence'],
                    source="ML_MODEL"
                )

        # ---- Fallback to rule-based ----
        ml_output = cls._rule_based_fallback(
            crop_name,
            growth_stage,
            growth_health_status,
            growth_alert_types,
            location_id
        )

        adjusted = cls._apply_safety_limits(
            base_thresholds,
            ml_output["thresholds"]
        )

        logger.info("✅ Rule-based adaptive thresholds applied")

        return AdaptiveThresholdResult(
            thresholds=adjusted,
            confidence=ml_output["confidence"],
            source="RULE_BASED"
        )

    # ---------------- RULE-BASED FALLBACK ---------------- #

    @classmethod
    def _rule_based_fallback(
        cls,
        crop_name: str,
        growth_stage: str,
        growth_health_status: str,
        growth_alert_types: list[str],
        location_id: str
    ) -> dict:

        crop_name = crop_name.lower()
        growth_stage = growth_stage.lower()

        # Healthy crop → relax thresholds slightly
        if (
            crop_name == "cotton"
            and growth_stage == "vegetative"
            and growth_health_status == "NORMAL"
            and "SLOW_GROWTH" not in growth_alert_types
        ):
            return {
                "thresholds": {
                    "heat_stress_temp": 37.0,
                    "heavy_rain_mm": 25.0,
                    "high_wind_kmh": 18.0,
                    "low_temp_threshold": 8.0,
                    "drought_days_threshold": 7.0
                },
                "confidence": 0.82
            }

        # Wheat in vegetative stage
        if (
            crop_name == "wheat"
            and growth_stage in ["seedling", "tillering"]
            and growth_health_status == "NORMAL"
        ):
            return {
                "thresholds": {
                    "heat_stress_temp": 35.0,
                    "heavy_rain_mm": 20.0,
                    "high_wind_kmh": 16.0,
                    "low_temp_threshold": 6.0,
                    "drought_days_threshold": 5.0
                },
                "confidence": 0.78
            }

        # Already stressed crop → earlier alerts
        if growth_health_status in ["SLOW", "ABNORMAL"]:
            return {
                "thresholds": {
                    "heat_stress_temp": 34.0,
                    "heavy_rain_mm": 18.0,
                    "high_wind_kmh": 14.0,
                    "low_temp_threshold": 8.0,
                    "drought_days_threshold": 4.0
                },
                "confidence": 0.75
            }

        # Default fallback
        return {
            "thresholds": {
                "heat_stress_temp": 36.0,
                "heavy_rain_mm": 22.0,
                "high_wind_kmh": 17.0,
                "low_temp_threshold": 7.0,
                "drought_days_threshold": 6.0
            },
            "confidence": 0.65
        }

    # ---------------- SAFETY CLAMP ---------------- #

    @classmethod
    def _apply_safety_limits(
        cls,
        base: Dict[str, float],
        proposed: Dict[str, float]
    ) -> Dict[str, float]:

        final = base.copy()

        for key, value in proposed.items():
            if key not in cls.HARD_LIMITS:
                continue

            min_v, max_v = cls.HARD_LIMITS[key]
            final[key] = max(min_v, min(max_v, value))

            logger.info(f"🔒 {key}: {base[key]} → {final[key]}")

        return final
    
    @classmethod
    def train_model(cls, training_data: list, model_path: str = None):
        """Train the ML model with historical data"""
        try:
            if cls.ml_model is None:
                cls.ml_model = AdaptiveThresholdMLModel(model_path)
            
            metrics = cls.ml_model.train(training_data)
            logger.success("🎉 ML Model training completed!")
            return metrics
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {}
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get information about the current ML model"""
        if cls.ml_model is None:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized" if cls.ml_model.is_trained else "not_trained",
            "model_path": cls.ml_model.model_path,
            "threshold_types": cls.ml_model.threshold_types,
            "feature_count": len(cls.ml_model.feature_columns) if cls.ml_model.feature_columns else 0
        }
