from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.core.base_agent.output_schema import (
    StandardizedAgentOutput,
    AgentDecision,
    StructuredRecommendation,
    StructuredWarning,
    create_agent_decision,
    create_structured_recommendation,
    create_structured_warning
)
from farmxpert.services.tools import WeatherMonitoringTool, AlertSystemTool, WeatherTool
from farmxpert.agents.operations.weather_watcher.agent import WeatherWatcherAgent as AppWeatherWatcherAgent


class WeatherWatcherAgent(EnhancedBaseAgent):
    name = "weather_watcher"
    description = "Monitors weather conditions and issues time-sensitive guidance with real-time alerts"

    def _get_system_prompt(self) -> str:
        return """You are a Weather Watcher Agent specializing in real-time weather monitoring and alert systems for farming.

Your expertise includes:
- Real-time weather data analysis and forecasting
- Weather alert system management and notifications
- Time-sensitive farming activity recommendations
- Weather risk assessment and early warning systems
- Seasonal weather pattern analysis and predictions
- Climate-adaptive farming strategies

Always provide practical, time-sensitive recommendations with real-time alerts based on current and forecasted weather conditions."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "Should I apply fertilizer today?",
                "output": "Based on real-time weather data, I recommend postponing fertilizer application as heavy rain (25mm) is expected tomorrow. I've sent you an alert notification. The optimal time would be after the rain stops, around 2-3 days from now."
            },
            {
                "input": "When is the best time to spray pesticides?",
                "output": "Current weather conditions show low wind (5 km/h) and moderate humidity (65%). This is ideal for pesticide spraying. I recommend spraying between 6-8 AM tomorrow. I'll send you a reminder alert 30 minutes before the optimal window."
            }
        ]

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather monitoring using the improved app weather watcher implementation (no LLM)."""
        try:
            context = inputs.get("context", {})

            location = context.get("location")
            if not isinstance(location, dict):
                location = inputs.get("location")
            if not isinstance(location, dict):
                location = {}

            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if not latitude or not longitude:
                def _extract_location_from_query(q: str) -> str:
                    text = (q or "").strip()
                    if not text:
                        return ""

                    lowered = text.lower()
                    for token in [" for ", " in "]:
                        if token in lowered:
                            idx = lowered.rfind(token)
                            candidate = text[idx + len(token):].strip(" .,:;\n\t")
                            if candidate:
                                return candidate

                    # Fallback: if query contains a comma, take the last 1-2 segments
                    if "," in text:
                        parts = [p.strip() for p in text.split(",") if p.strip()]
                        if len(parts) >= 2:
                            return ", ".join(parts[-2:])
                        if parts:
                            return parts[-1]

                    return text

                location_text = (
                    context.get("location_text")
                    or context.get("region")
                    or inputs.get("location_text")
                    or inputs.get("region")
                    or inputs.get("location")
                )
                if not isinstance(location_text, str) or not location_text.strip():
                    location_text = inputs.get("query")
                location_text = _extract_location_from_query(location_text) if isinstance(location_text, str) else ""
                location_text = (location_text or "").strip()

                if location_text:
                    forecast = await WeatherTool.get_weather_forecast(location_text, days=7)
                    if not isinstance(forecast, dict) or forecast.get("error"):
                        return {
                            "agent": self.name,
                            "success": False,
                            "response": "Weather fetch failed",
                            "data": {"location": {"text": location_text}, "raw": forecast},
                            "recommendations": [],
                            "warnings": [],
                            "metadata": {"model": "deterministic"},
                        }

                    daily_raw = forecast.get("daily_forecast")
                    daily_list = daily_raw if isinstance(daily_raw, list) else []
                    alerts_raw = (forecast.get("agricultural_impact") or {}).get("alerts")
                    alerts_dict = alerts_raw if isinstance(alerts_raw, dict) else {}
                    response_text = "Weather analysis complete"
                    heat = (alerts_dict.get("heat_stress") or {}).get("active")
                    dry = (alerts_dict.get("dry_spell") or {}).get("active")
                    if heat or dry:
                        parts = []
                        if heat:
                            parts.append("Heat stress risk")
                        if dry:
                            parts.append("Dry spell risk")
                        response_text = ", ".join(parts)
                    
                    # Build structured recommendations from farming_recommendations
                    farming_recs = forecast.get("farming_recommendations") or []
                    structured_recommendations: List[StructuredRecommendation] = []
                    for i, rec in enumerate(farming_recs[:4]):
                        structured_recommendations.append(create_structured_recommendation(
                            action=rec,
                            reason="Based on weather forecast analysis",
                            timeline="as conditions permit",
                            priority=i + 1,
                            category="weather"
                        ))
                    
                    # Build structured warnings from alerts
                    structured_warnings: List[StructuredWarning] = []
                    if heat:
                        structured_warnings.append(create_structured_warning(
                            issue="Heat stress risk detected",
                            severity="high" if heat else "medium",
                            category="weather"
                        ))
                    if dry:
                        structured_warnings.append(create_structured_warning(
                            issue="Dry spell risk detected",
                            severity="medium",
                            category="weather"
                        ))
                    
                    decision = create_agent_decision(
                        summary=f"Weather forecast for {location_text}: {response_text}. {len(daily_list)} days forecast.",
                        confidence=0.85
                    )
                    
                    return StandardizedAgentOutput(
                        agent=self.name,
                        success=True,
                        decision=decision,
                        recommendations=structured_recommendations,
                        warnings=structured_warnings,
                        data={
                            "location": {"text": location_text},
                            "forecast": {"days": daily_list, "count": len(daily_list)},
                            "alerts": alerts_dict,
                            "raw": forecast,
                        },
                        metadata={"model": "deterministic", "provider": forecast.get("provider") or "unknown"}
                    ).to_dict()

            result = AppWeatherWatcherAgent.analyze_weather(location)
            ok = bool(result.get("success")) if isinstance(result, dict) else False
            data = result.get("data") if isinstance(result, dict) else None

            weather = data.get("weather") if isinstance(data, dict) else None
            temp = weather.get("temperature") if isinstance(weather, dict) else None
            cond = weather.get("weather_condition") if isinstance(weather, dict) else None
            response_text = f"Temperature: {temp}°C, {cond}" if temp is not None and cond else "Weather analysis complete"
            
            decision = create_agent_decision(
                summary=response_text,
                confidence=0.8 if ok else 0.5
            )
            
            return StandardizedAgentOutput(
                agent=self.name,
                success=ok,
                decision=decision,
                recommendations=[],
                warnings=[],
                data=data if data else {},
                metadata={"model": "deterministic"}
            ).to_dict()
        except Exception as e:
            self.logger.error(f"Error in weather watcher agent: {e}")
            
            decision = create_agent_decision(
                summary="Weather analysis failed",
                confidence=0.0
            )
            
            return StandardizedAgentOutput(
                agent=self.name,
                success=False,
                decision=decision,
                recommendations=[],
                warnings=[],
                data={},
                error={"message": str(e), "type": "exception"},
                metadata={"model": "deterministic"}
            ).to_dict()

    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather analysis using traditional logic"""
        query = inputs.get("query", "")
        location = inputs.get("location", "unknown")
        planned_activities = inputs.get("planned_activities", [])
        entities = inputs.get("entities", {})
        
        # Generate weather forecast (in real implementation, this would call weather API)
        forecast = self._generate_weather_forecast(location)
        
        # Analyze weather for farming activities
        analysis = self._analyze_weather_for_farming(forecast, planned_activities)
        
        # Generate recommendations and alerts
        recommendations = self._generate_weather_recommendations(forecast, analysis)
        alerts = self._generate_weather_alerts(forecast, analysis)
        insights = self._generate_weather_insights(forecast, location)
        
        # Determine best farming window
        best_window = self._determine_best_farming_window(forecast)
        
        # Build structured recommendations
        structured_recommendations: List[StructuredRecommendation] = []
        for i, rec in enumerate(recommendations):
            structured_recommendations.append(create_structured_recommendation(
                action=rec,
                reason="Based on weather forecast analysis",
                timeline=best_window,
                priority=i + 1,
                category="weather"
            ))
        
        # Build structured warnings from alerts
        structured_warnings: List[StructuredWarning] = []
        for alert in alerts:
            severity = "high" if "warning" in alert.lower() else "medium"
            structured_warnings.append(create_structured_warning(
                issue=alert,
                severity=severity,
                category="weather"
            ))
        
        decision = create_agent_decision(
            summary=f"Weather for {location}: {analysis['summary']}. Risk: {analysis.get('risk_level', 'low')}",
            details=f"Best farming window: {best_window}. Insights: {', '.join(insights)}",
            confidence=0.85 if analysis.get('risk_level') == 'low' else 0.7
        )
        
        return StandardizedAgentOutput(
            agent=self.name,
            success=True,
            decision=decision,
            recommendations=structured_recommendations,
            warnings=structured_warnings,
            data={
                "location": location,
                "weather_forecast": forecast,
                "analysis": analysis,
                "best_farming_window": best_window,
                "weather_risk_level": analysis.get("risk_level", "low")
            },
            metadata={"source": "traditional"}
        ).to_dict()

    def _generate_weather_forecast(self, location: str) -> Dict[str, Any]:
        """Generate weather forecast (mock data - in real implementation, call weather API)"""
        # This is mock data - in production, integrate with weather APIs like OpenWeatherMap
        base_temp = 25
        base_humidity = 70
        base_wind = 10
        
        # Simulate seasonal variations
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:  # Winter
            base_temp -= 5
            base_humidity += 10
        elif current_month in [6, 7, 8, 9]:  # Monsoon
            base_temp += 2
            base_humidity += 15
            base_wind += 5
        
        forecast = {
            "today": {
                "temp": base_temp,
                "humidity": base_humidity,
                "precipitation": 0,
                "wind": base_wind,
                "condition": "partly_cloudy"
            },
            "tomorrow": {
                "temp": base_temp - 2,
                "humidity": base_humidity + 10,
                "precipitation": 15 if current_month in [6, 7, 8, 9] else 5,
                "wind": base_wind + 3,
                "condition": "rainy" if current_month in [6, 7, 8, 9] else "cloudy"
            },
            "day_after": {
                "temp": base_temp - 1,
                "humidity": base_humidity + 5,
                "precipitation": 25 if current_month in [6, 7, 8, 9] else 10,
                "wind": base_wind + 2,
                "condition": "rainy" if current_month in [6, 7, 8, 9] else "partly_cloudy"
            }
        }
        
        return forecast

    def _analyze_weather_for_farming(self, forecast: Dict[str, Any], planned_activities: List[str]) -> Dict[str, Any]:
        """Analyze weather conditions for farming activities"""
        analysis = {
            "summary": "",
            "risk_level": "low",
            "suitable_activities": [],
            "unsuitable_activities": [],
            "weather_concerns": []
        }
        
        today = forecast["today"]
        tomorrow = forecast["tomorrow"]
        
        # Analyze precipitation
        if tomorrow["precipitation"] > 10:
            analysis["weather_concerns"].append("Rain expected tomorrow")
            analysis["unsuitable_activities"].extend(["fertilizer_application", "pesticide_spraying"])
            analysis["risk_level"] = "medium"
        
        if today["precipitation"] > 5:
            analysis["weather_concerns"].append("Current rain conditions")
            analysis["unsuitable_activities"].extend(["field_work", "harvesting"])
        
        # Analyze wind conditions
        if today["wind"] > 15:
            analysis["weather_concerns"].append("High wind conditions")
            analysis["unsuitable_activities"].extend(["pesticide_spraying", "aerial_application"])
            analysis["risk_level"] = "high" if analysis["risk_level"] == "low" else "high"
        
        # Analyze temperature
        if today["temp"] > 35:
            analysis["weather_concerns"].append("High temperature")
            analysis["unsuitable_activities"].extend(["manual_labor", "transplanting"])
        
        # Determine suitable activities
        if today["precipitation"] == 0 and today["wind"] < 15:
            analysis["suitable_activities"].extend(["field_preparation", "planting", "irrigation"])
        
        if tomorrow["precipitation"] > 20:
            analysis["suitable_activities"].append("post_rain_activities")
        
        # Generate summary
        if analysis["weather_concerns"]:
            analysis["summary"] = f"Weather concerns: {', '.join(analysis['weather_concerns'])}"
        else:
            analysis["summary"] = "Favorable weather conditions for most farming activities"
        
        return analysis

    def _generate_weather_recommendations(self, forecast: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate weather-based recommendations"""
        recommendations = []
        
        tomorrow = forecast["tomorrow"]
        today = forecast["today"]
        
        # Rain-based recommendations
        if tomorrow["precipitation"] > 10:
            recommendations.append("Postpone fertilizer application - rain expected tomorrow")
            if tomorrow["precipitation"] > 20:
                recommendations.append("Good time for transplanting after rain")
        
        # Wind-based recommendations
        if today["wind"] > 15:
            recommendations.append("Avoid pesticide spraying due to high wind")
        elif today["wind"] < 5:
            recommendations.append("Ideal conditions for pesticide application")
        
        # Temperature-based recommendations
        if today["temp"] > 35:
            recommendations.append("Schedule field work for early morning or evening")
        elif 20 <= today["temp"] <= 30:
            recommendations.append("Optimal temperature for most farming activities")
        
        # Humidity-based recommendations
        if today["humidity"] > 80:
            recommendations.append("High humidity - monitor for fungal diseases")
        elif today["humidity"] < 40:
            recommendations.append("Low humidity - ensure adequate irrigation")
        
        return recommendations[:4]  # Limit to 4 recommendations

    def _generate_weather_alerts(self, forecast: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate weather alerts"""
        alerts = []
        
        tomorrow = forecast["tomorrow"]
        today = forecast["today"]
        
        # Precipitation alerts
        if tomorrow["precipitation"] > 15:
            alerts.append(f"Rain alert: {tomorrow['precipitation']}mm expected tomorrow")
        
        # Wind alerts
        if today["wind"] > 20:
            alerts.append("High wind warning: Avoid outdoor activities")
        elif today["wind"] > 15:
            alerts.append("Moderate wind: Be cautious with spraying activities")
        
        # Temperature alerts
        if today["temp"] > 40:
            alerts.append("Heat wave warning: Avoid outdoor work during peak hours")
        elif today["temp"] < 5:
            alerts.append("Frost warning: Protect sensitive crops")
        
        # Humidity alerts
        if today["humidity"] > 90:
            alerts.append("Very high humidity: Risk of fungal diseases")
        
        return alerts[:3]  # Limit to 3 alerts

    def _generate_weather_insights(self, forecast: Dict[str, Any], location: str) -> List[str]:
        """Generate weather insights"""
        insights = []
        
        # Seasonal insights
        current_month = datetime.now().month
        if current_month in [6, 7, 8, 9]:
            insights.append("Monsoon season: Plan for water management and disease prevention")
        elif current_month in [12, 1, 2]:
            insights.append("Winter season: Focus on cold-resistant crops and frost protection")
        elif current_month in [3, 4, 5]:
            insights.append("Summer season: Ensure adequate irrigation and heat management")
        
        # Weather pattern insights
        if forecast["tomorrow"]["precipitation"] > forecast["today"]["precipitation"]:
            insights.append("Increasing precipitation trend - plan accordingly")
        
        if forecast["today"]["wind"] > 12:
            insights.append("Windy conditions - consider wind-resistant crop varieties")
        
        return insights[:2]  # Limit to 2 insights

    def _determine_best_farming_window(self, forecast: Dict[str, Any]) -> str:
        """Determine the best time window for farming activities"""
        today = forecast["today"]
        
        # Check current conditions
        if today["precipitation"] > 5:
            return "Wait for rain to stop"
        elif today["wind"] > 15:
            return "Early morning (6-8 AM) when wind is calmer"
        elif today["temp"] > 35:
            return "Early morning (6-10 AM) or evening (4-6 PM)"
        else:
            return "Today morning (6-10 AM) - optimal conditions"
    
    def _extract_recommendations_from_data(self, weather_data: Dict[str, Any], alert_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from weather and alert data"""
        recommendations = []
        
        if isinstance(weather_data, dict):
            if "agricultural_indices" in weather_data:
                recommendations.append("Agricultural weather indices analyzed")
            
            if "daily_forecast" in weather_data:
                recommendations.append("Daily weather forecast available")
        
        if isinstance(alert_data, dict):
            if "recommended_actions" in alert_data:
                recommendations.append("Weather-based action recommendations provided")
            
            if "crop_protection" in alert_data:
                recommendations.append("Crop protection recommendations available")
        
        return recommendations
    
    def _extract_warnings_from_data(self, alert_data: Dict[str, Any], weather_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from alert and weather data"""
        warnings = []
        
        if isinstance(alert_data, dict):
            if "active_alerts" in alert_data:
                alerts = alert_data["active_alerts"]
                if isinstance(alerts, list) and alerts:
                    warnings.append(f"Active weather alerts: {', '.join(alerts[:2])}")
            
            if "severity_levels" in alert_data:
                severity = alert_data["severity_levels"]
                if isinstance(severity, list) and severity:
                    high_severity = [s for s in severity if isinstance(s, str) and s.lower() in ["high", "severe", "extreme"]]
                    if high_severity:
                        warnings.append(f"High severity alerts: {', '.join(high_severity[:2])}")
        
        if isinstance(weather_data, dict):
            if "weather_alerts" in weather_data:
                weather_alerts = weather_data["weather_alerts"]
                if isinstance(weather_alerts, list) and weather_alerts:
                    warnings.append(f"Weather warnings: {', '.join(weather_alerts[:2])}")
        
        return warnings
