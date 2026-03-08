from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger

from ..models.weather_models import WeatherSnapshot, WeatherForecast
from ..models.output_models import WeatherAlertOutput, RiskAlert, FarmingAction, WeatherSummary
from ..constants.thresholds import (
    HEAT_STRESS_TEMP,
    COLD_STRESS_TEMP,
    HEAVY_RAIN_MM,
    HIGH_WIND_KMH,
    ALERT_COOLDOWN_MINUTES,
    DRY_SPELL_RAIN_MM,
    CONSECUTIVE_DRY_DAYS,
    HIGH_RAIN_PROBABILITY,
    LOW_RAIN_PROBABILITY
)


class RuleEngine:
    """
    Enhanced rule engine for Weather Watcher with farming intelligence
    """

    def __init__(self, last_alerts: dict):
        """
        last_alerts format:
        {
            "HEAT_STRESS": datetime,
            "HEAVY_RAIN": datetime,
            "DRY_SPELL": datetime,
            "HIGH_WIND": datetime
        }
        """
        self.last_alerts = last_alerts

    # ---------------- PUBLIC ---------------- #

    def evaluate(self, current_weather: WeatherSnapshot, forecasts: List[WeatherForecast] = None) -> WeatherAlertOutput:
        """
        Evaluate weather conditions and generate comprehensive farming intelligence
        """
        if forecasts is None:
            forecasts = []
        
        # Generate weather summary
        weather_summary = self._generate_weather_summary(current_weather, forecasts)
        
        # Generate risk alerts
        risk_alerts = []
        
        # Check current conditions
        heat_alert = self._heat_stress_rule(current_weather)
        if heat_alert:
            risk_alerts.append(heat_alert)
        
        rain_alert = self._rainfall_rule(current_weather)
        if rain_alert:
            risk_alerts.append(rain_alert)
        
        wind_alert = self._wind_rule(current_weather)
        if wind_alert:
            risk_alerts.append(wind_alert)
        
        # Check forecast conditions
        if forecasts:
            dry_spell_alert = self._dry_spell_rule(forecasts)
            if dry_spell_alert:
                risk_alerts.append(dry_spell_alert)
            
            high_rain_alert = self._high_rain_probability_rule(forecasts)
            if high_rain_alert:
                risk_alerts.append(high_rain_alert)
        
        # Generate actionable farming advice
        farming_actions = self._generate_farming_actions(current_weather, forecasts, risk_alerts)
        
        return WeatherAlertOutput(
            weather_summary=weather_summary,
            risk_alerts=risk_alerts,
            farming_actions=farming_actions,
            location_info=None,  # Will be set by agent
            generated_at=datetime.utcnow()
        )

    # ---------------- WEATHER SUMMARY ---------------- #

    def _generate_weather_summary(self, current: WeatherSnapshot, forecasts: List[WeatherForecast]) -> WeatherSummary:
        """Generate farmer-friendly weather summary"""
        temp_desc = self._describe_temperature(current.temperature)
        condition_desc = self._describe_condition(current.weather_condition, current.rainfall_probability)
        
        # Rainfall outlook based on forecasts
        if forecasts:
            total_rain = sum(f.rainfall_mm for f in forecasts[:3])  # Next 3 days
            if total_rain > 15:
                rain_outlook = "Heavy rainfall expected in next few days"
            elif total_rain > 5:
                rain_outlook = "Moderate rainfall expected"
            elif total_rain > 0:
                rain_outlook = "Light rainfall possible"
            else:
                rain_outlook = "Dry conditions expected"
        else:
            rain_outlook = "No forecast data available"
        
        return WeatherSummary(
            temperature=temp_desc,
            condition=condition_desc,
            rainfall_outlook=rain_outlook
        )

    def _describe_temperature(self, temp: float) -> str:
        """Describe temperature in farmer-friendly terms"""
        if temp >= 40:
            return f"Very hot ({temp:.1f}°C) - dangerous heat levels"
        elif temp >= 35:
            return f"Hot ({temp:.1f}°C) - heat stress conditions"
        elif temp >= 25:
            return f"Warm ({temp:.1f}°C) - good for most crops"
        elif temp >= 15:
            return f"Mild ({temp:.1f}°C) - comfortable conditions"
        elif temp >= 5:
            return f"Cool ({temp:.1f}°C) - some crops may struggle"
        else:
            return f"Very cold ({temp:.1f}°C) - frost risk"

    def _describe_condition(self, condition: str, rain_prob: float) -> str:
        """Describe weather condition in simple terms"""
        if rain_prob > 0.7:
            return f"Rain very likely ({rain_prob*100:.0f}% chance)"
        elif rain_prob > 0.4:
            return f"Rain possible ({rain_prob*100:.0f}% chance)"
        elif condition == "clear":
            return "Clear skies"
        elif condition in ["clouds", "cloudy"]:
            return "Cloudy"
        elif condition in ["rain", "drizzle"]:
            return "Rainy"
        elif condition in ["thunderstorm"]:
            return "Thunderstorms"
        else:
            return condition.capitalize()

    # ---------------- RISK ALERTS ---------------- #

    def _heat_stress_rule(self, weather: WeatherSnapshot) -> Optional[RiskAlert]:
        """Check for heat stress conditions"""
        if weather.max_temperature < HEAT_STRESS_TEMP:
            return None

        if not self._cooldown_passed("HEAT_STRESS"):
            return None

        logger.warning("🔥 Heat stress rule triggered")
        self.last_alerts["HEAT_STRESS"] = datetime.utcnow()

        severity = "HIGH" if weather.max_temperature >= 40 else "MEDIUM"
        confidence = 0.9 if weather.max_temperature >= 40 else 0.8

        return RiskAlert(
            alert_type="HEAT_STRESS",
            severity=severity,
            message=f"High temperature ({weather.max_temperature:.1f}°C) may cause heat stress to crops and livestock",
            confidence=confidence
        )

    def _rainfall_rule(self, weather: WeatherSnapshot) -> Optional[RiskAlert]:
        """Check for heavy rainfall conditions"""
        if weather.rainfall_mm < HEAVY_RAIN_MM:
            return None

        if not self._cooldown_passed("HEAVY_RAIN"):
            return None

        logger.warning("🌧️ Heavy rain rule triggered")
        self.last_alerts["HEAVY_RAIN"] = datetime.utcnow()

        severity = "HIGH" if weather.rainfall_mm >= 20 else "MEDIUM"
        confidence = 0.85

        return RiskAlert(
            alert_type="HEAVY_RAIN",
            severity=severity,
            message=f"Heavy rainfall ({weather.rainfall_mm:.1f}mm) may cause waterlogging and soil erosion",
            confidence=confidence
        )

    def _wind_rule(self, weather: WeatherSnapshot) -> Optional[RiskAlert]:
        """Check for high wind conditions"""
        if weather.wind_speed < HIGH_WIND_KMH:
            return None

        if not self._cooldown_passed("HIGH_WIND"):
            return None

        logger.warning("🌬️ High wind rule triggered")
        self.last_alerts["HIGH_WIND"] = datetime.utcnow()

        severity = "HIGH" if weather.wind_speed >= 70 else "MEDIUM"
        confidence = 0.8

        return RiskAlert(
            alert_type="HIGH_WIND",
            severity=severity,
            message=f"Strong winds ({weather.wind_speed:.1f} km/h) may damage crops and affect spraying",
            confidence=confidence
        )

    def _dry_spell_rule(self, forecasts: List[WeatherForecast]) -> Optional[RiskAlert]:
        """Check for consecutive dry days in forecast"""
        if len(forecasts) < CONSECUTIVE_DRY_DAYS:
            return None

        if not self._cooldown_passed("DRY_SPELL"):
            return None

        # Count consecutive dry days
        consecutive_dry = 0
        for forecast in forecasts:
            if forecast.rainfall_mm < DRY_SPELL_RAIN_MM and forecast.rainfall_probability < LOW_RAIN_PROBABILITY:
                consecutive_dry += 1
            else:
                break
        
        if consecutive_dry < CONSECUTIVE_DRY_DAYS:
            return None

        logger.warning(f"🏜️ Dry spell rule triggered: {consecutive_dry} consecutive dry days")
        self.last_alerts["DRY_SPELL"] = datetime.utcnow()

        severity = "HIGH" if consecutive_dry >= 5 else "MEDIUM"
        confidence = 0.8

        return RiskAlert(
            alert_type="DRY_SPELL",
            severity=severity,
            message=f"Dry spell expected: {consecutive_dry} consecutive days with minimal rainfall",
            confidence=confidence
        )

    def _high_rain_probability_rule(self, forecasts: List[WeatherForecast]) -> Optional[RiskAlert]:
        """Check for high rainfall probability in next few days"""
        high_rain_days = sum(1 for f in forecasts[:3] if f.rainfall_probability > HIGH_RAIN_PROBABILITY)
        
        if high_rain_days < 2:  # Need at least 2 days with high rain probability
            return None

        if not self._cooldown_passed("HIGH_RAIN_PROB"):
            return None

        logger.warning(f"🌧️ High rain probability rule triggered: {high_rain_days} days")
        self.last_alerts["HIGH_RAIN_PROB"] = datetime.utcnow()

        severity = "HIGH" if high_rain_days >= 3 else "MEDIUM"
        confidence = 0.75

        return RiskAlert(
            alert_type="HIGH_RAIN_PROBABILITY",
            severity=severity,
            message=f"High rainfall probability expected for {high_rain_days} of the next 3 days",
            confidence=confidence
        )

    # ---------------- FARMING ACTIONS ---------------- #

    def _generate_farming_actions(self, current: WeatherSnapshot, forecasts: List[WeatherForecast], alerts: List[RiskAlert]) -> List[FarmingAction]:
        """Generate actionable farming advice based on conditions"""
        actions = []
        
        # Heat stress actions
        if any(a.alert_type == "HEAT_STRESS" for a in alerts):
            actions.extend([
                FarmingAction(
                    action="Increase irrigation frequency during early morning or evening",
                    reason="High temperatures increase water needs and prevent crop stress",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Avoid field work during peak heat hours (11 AM - 3 PM)",
                    reason="Protect yourself and livestock from heat exhaustion",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Provide shade for young plants and livestock",
                    reason="Prevent heat damage and reduce stress",
                    priority="MEDIUM"
                )
            ])
        
        # Heavy rain actions
        if any(a.alert_type == "HEAVY_RAIN" for a in alerts):
            actions.extend([
                FarmingAction(
                    action="Stop all irrigation immediately",
                    reason="Prevent waterlogging and root damage",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Check and improve field drainage",
                    reason="Remove excess water and prevent soil erosion",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Delay sowing and transplanting",
                    reason="Seeds may wash away and young plants may drown",
                    priority="MEDIUM"
                ),
                FarmingAction(
                    action="Postpone pesticide and fertilizer application",
                    reason="Rain will wash away chemicals and waste money",
                    priority="MEDIUM"
                )
            ])
        
        # Dry spell actions
        if any(a.alert_type == "DRY_SPELL" for a in alerts):
            actions.extend([
                FarmingAction(
                    action="Conserve water through mulching",
                    reason="Reduce soil evaporation and maintain moisture",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Plan supplemental irrigation",
                    reason="Maintain crop water requirements during dry period",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Consider drought-resistant crops for next season",
                    reason="Prepare for future water scarcity",
                    priority="MEDIUM"
                )
            ])
        
        # High rain probability actions
        if any(a.alert_type == "HIGH_RAIN_PROBABILITY" for a in alerts):
            actions.extend([
                FarmingAction(
                    action="Delay sowing if rain expected within 2-3 days",
                    reason="Seeds need proper conditions to germinate",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Prepare covered storage for harvested crops",
                    reason="Protect harvest from unexpected rain damage",
                    priority="MEDIUM"
                ),
                FarmingAction(
                    action="Check and repair farm equipment before rain",
                    reason="Wet conditions make equipment maintenance difficult",
                    priority="LOW"
                )
            ])
        
        # High wind actions
        if any(a.alert_type == "HIGH_WIND" for a in alerts):
            actions.extend([
                FarmingAction(
                    action="Postpone pesticide spraying",
                    reason="Wind causes spray drift and reduces effectiveness",
                    priority="HIGH"
                ),
                FarmingAction(
                    action="Secure loose materials and protect young plants",
                    reason="Prevent damage from strong winds",
                    priority="MEDIUM"
                )
            ])
        
        # General weather-based actions
        if current.temperature > 30 and current.humidity < 40:
            actions.append(FarmingAction(
                action="Monitor for pest infestations in hot, dry conditions",
                reason="Pests thrive in hot, dry weather",
                priority="MEDIUM"
            ))
        
        # If no specific alerts, provide general advice
        if not actions:
            if current.temperature >= 20 and current.temperature <= 30 and current.rainfall_mm < 5:
                actions.append(FarmingAction(
                    action="Good conditions for most farming activities",
                    reason="Weather is favorable for field work",
                    priority="LOW"
                ))
        
        return actions

    # ---------------- UTILS ---------------- #

    def _cooldown_passed(self, alert_type: str) -> bool:
        last_time = self.last_alerts.get(alert_type)

        if not last_time:
            return True

        return datetime.utcnow() - last_time > timedelta(
            minutes=ALERT_COOLDOWN_MINUTES
        )
