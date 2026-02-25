"""
Farmer-facing response layer for Weather Watcher Agent
Converts structured outputs into simple, actionable farmer messages
"""

from typing import Dict, Any, List
from datetime import datetime

from ..models.output_models import WeatherAlertOutput, RiskAlert, FarmingAction


class SeasonalValidator:
    """
    Applies seasonal validation rules for Indian weather intelligence
    """
    
    @staticmethod
    def get_season(month: int) -> str:
        """Get season based on month"""
        if month in [12, 1, 2]:  # Dec-Feb
            return "winter"
        elif month in [3, 4, 5]:  # Mar-May
            return "summer"
        elif month in [6, 7, 8, 9]:  # Jun-Sep
            return "monsoon"
        else:  # Oct-Nov
            return "post_monsoon"
    
    @staticmethod
    def validate_risks(risk_alerts: List[RiskAlert], season: str) -> List[RiskAlert]:
        """Remove seasonally impossible risks"""
        valid_risks = []
        
        for risk in risk_alerts:
            risk_type = risk.alert_type.lower()
            
            # Winter (Dec-Feb): NO heat stress, NO monsoon rain
            if season == "winter":
                if "heat" in risk_type or "monsoon" in risk_type:
                    continue
            
            # Summer (Mar-May): NO monsoon rain
            elif season == "summer":
                if "monsoon" in risk_type:
                    continue
            
            # Monsoon (Jun-Sep): NO dry spell, NO heat stress
            elif season == "monsoon":
                if "dry" in risk_type or "heat" in risk_type:
                    continue
            
            valid_risks.append(risk)
        
        return valid_risks
    
    @staticmethod
    def remove_contradictions(risk_alerts: List[RiskAlert]) -> List[RiskAlert]:
        """Remove contradictory risks (heavy rain and dry spell)"""
        has_heavy_rain = any("heavy" in risk.alert_type.lower() or "rain" in risk.alert_type.lower() 
                           for risk in risk_alerts)
        has_dry_spell = any("dry" in risk.alert_type.lower() for risk in risk_alerts)
        
        if has_heavy_rain and has_dry_spell:
            # Remove dry spell if heavy rain present
            return [risk for risk in risk_alerts if "dry" not in risk.alert_type.lower()]
        
        return risk_alerts
    
    @staticmethod
    def limit_risks(risk_alerts: List[RiskAlert]) -> List[RiskAlert]:
        """Limit to max 1 HIGH and 1 MEDIUM risk"""
        high_risks = [risk for risk in risk_alerts if risk.severity.upper() == "HIGH"]
        medium_risks = [risk for risk in risk_alerts if risk.severity.upper() == "MEDIUM"]
        
        selected = []
        if high_risks:
            selected.append(high_risks[0])  # Take first HIGH risk
        if medium_risks:
            selected.append(medium_risks[0])  # Take first MEDIUM risk
        
        return selected
    
    @staticmethod
    def remove_conflicting_actions(farming_actions: List[FarmingAction]) -> List[FarmingAction]:
        """Remove conflicting irrigation advice"""
        irrigation_increase = any("increase" in action.action.lower() or "water" in action.action.lower() 
                                for action in farming_actions)
        irrigation_stop = any("stop" in action.action.lower() or "reduce" in action.action.lower() 
                            for action in farming_actions)
        
        if irrigation_increase and irrigation_stop:
            # Remove stop irrigation actions if increase present
            return [action for action in farming_actions 
                   if not ("stop" in action.action.lower() or "reduce" in action.action.lower())]
        
        return farming_actions
    
    @staticmethod
    def filter_actions_by_risks(farming_actions: List[FarmingAction], valid_risks: List[RiskAlert]) -> List[FarmingAction]:
        """Keep only actions related to remaining risks"""
        if not valid_risks:
            return []
        
        # Keep actions that relate to the valid risks
        filtered_actions = []
        for action in farming_actions:
            action_lower = action.action.lower()
            reason_lower = action.reason.lower()
            
            for risk in valid_risks:
                risk_type = risk.alert_type.lower()
                
                # Heat stress related
                if "heat" in risk_type and ("heat" in action_lower or "hot" in action_lower or "shade" in action_lower):
                    filtered_actions.append(action)
                    break
                
                # Rain related
                elif "rain" in risk_type and ("rain" in action_lower or "drain" in action_lower or "stop" in action_lower):
                    filtered_actions.append(action)
                    break
                
                # Dry spell related
                elif "dry" in risk_type and ("water" in action_lower or "irrigat" in action_lower or "mulch" in action_lower):
                    filtered_actions.append(action)
                    break
        
        return filtered_actions


class FarmerMessageGenerator:
    """
    Converts structured weather intelligence into farmer-friendly messages
    """
    
    @staticmethod
    def generate_farmer_message(weather_result: WeatherAlertOutput, location_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate farmer-facing message from weather intelligence with seasonal validation
        
        Args:
            weather_result: Structured weather intelligence from agent
            location_info: Optional location details (village, district, state)
            
        Returns:
            Farmer-friendly message structure with seasonal validation
        """
        # Apply seasonal validation
        current_month = datetime.now().month
        season = SeasonalValidator.get_season(current_month)
        
        # Step 1: Validate risks by season
        valid_risks = SeasonalValidator.validate_risks(weather_result.risk_alerts, season)
        
        # Step 2: Remove contradictory risks
        valid_risks = SeasonalValidator.remove_contradictions(valid_risks)
        
        # Step 3: Limit risks (max 1 HIGH, 1 MEDIUM)
        valid_risks = SeasonalValidator.limit_risks(valid_risks)
        
        # Step 4: Filter actions by remaining risks
        filtered_actions = SeasonalValidator.filter_actions_by_risks(weather_result.farming_actions, valid_risks)
        
        # Step 5: Remove conflicting actions
        filtered_actions = SeasonalValidator.remove_conflicting_actions(filtered_actions)
        
        # Get location name for personalization
        location_name = FarmerMessageGenerator._get_location_name(location_info)
        
        # Generate message components
        title = f"🌦️ Weather Update for {location_name}"
        
        # Simple weather summary
        weather_summary = FarmerMessageGenerator._create_simple_summary(weather_result.weather_summary)
        
        # Risk alerts section (with validated risks)
        risk_alerts = FarmerMessageGenerator._create_risk_alerts_section(valid_risks)
        
        # Actionable advice section (with filtered actions)
        actionable_advice = FarmerMessageGenerator._create_actionable_advice_section(filtered_actions)
        
        return {
            "title": title,
            "weather_summary": weather_summary,
            "risk_alerts": risk_alerts,
            "actionable_advice": actionable_advice,
            "generated_at": weather_result.generated_at.strftime("%d %b %Y, %I:%M %p"),
            "location": location_name
        }
    
    @staticmethod
    def _get_location_name(location_info: Dict[str, Any] = None) -> str:
        """Get formatted location name"""
        if not location_info:
            return "Your Area"
        
        # Try village first, then district, then coordinates
        if location_info.get("village"):
            return location_info["village"]
        elif location_info.get("district"):
            return location_info["district"]
        elif location_info.get("latitude") and location_info.get("longitude"):
            return f"Your Location ({location_info['latitude']:.1f}°, {location_info['longitude']:.1f}°)"
        else:
            return "Your Area"
    
    @staticmethod
    def _create_simple_summary(weather_summary) -> str:
        """Create simple weather summary in plain language"""
        temp_desc = weather_summary.temperature
        
        # Convert technical terms to simple language
        if "heat stress" in temp_desc.lower():
            temp_simple = "Very hot weather"
        elif "hot" in temp_desc.lower():
            temp_simple = "Hot weather"
        elif "warm" in temp_desc.lower():
            temp_simple = "Pleasant weather"
        elif "cool" in temp_desc.lower():
            temp_simple = "Cool weather"
        elif "cold" in temp_desc.lower():
            temp_simple = "Cold weather"
        else:
            temp_simple = temp_desc
        
        # Simplify condition description
        condition = weather_summary.condition
        if "rain very likely" in condition.lower():
            condition_simple = "Rain expected"
        elif "rain possible" in condition.lower():
            condition_simple = "Some rain possible"
        elif "clear" in condition.lower():
            condition_simple = "Clear skies"
        elif "cloud" in condition.lower():
            condition_simple = "Cloudy weather"
        else:
            condition_simple = condition
        
        # Simplify rainfall outlook
        outlook = weather_summary.rainfall_outlook
        if "heavy rainfall" in outlook.lower():
            outlook_simple = "Heavy rain coming soon"
        elif "moderate rainfall" in outlook.lower():
            outlook_simple = "Some rain expected"
        elif "light rainfall" in outlook.lower():
            outlook_simple = "Light rain possible"
        elif "dry conditions" in outlook.lower():
            outlook_simple = "Dry weather ahead"
        else:
            outlook_simple = outlook
        
        return f"{temp_simple}. {condition_simple}. {outlook_simple}."
    
    @staticmethod
    def _create_risk_alerts_section(risk_alerts: List[RiskAlert]) -> Dict[str, Any]:
        """Create risk alerts section in farmer-friendly format"""
        if not risk_alerts:
            return {
                "has_alerts": False,
                "message": "No major weather risk"
            }
        
        alerts = []
        for alert in risk_alerts:
            # Convert alert types to simple language
            alert_name = FarmerMessageGenerator._convert_alert_type(alert.alert_type)
            
            # Convert severity to simple language
            severity_text = "High Risk" if alert.severity == "HIGH" else "Medium Risk"
            
            # Simplify message (remove technical terms)
            simple_message = FarmerMessageGenerator._simplify_alert_message(alert.message)
            
            alerts.append({
                "type": alert_name,
                "severity": severity_text,
                "message": simple_message
            })
        
        return {
            "has_alerts": True,
            "alerts": alerts
        }
    
    @staticmethod
    def _create_actionable_advice_section(farming_actions: List[FarmingAction]) -> List[Dict[str, Any]]:
        """Create actionable advice section with prioritized actions"""
        if not farming_actions:
            return [{
                "priority": "NORMAL",
                "action": "Weather conditions are currently normal for farming."
            }]
        
        # Sort by priority (HIGH first, then MEDIUM, then LOW)
        priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_actions = sorted(farming_actions, key=lambda x: priority_order.get(x.priority, 4))
        
        advice_list = []
        for action in sorted_actions:
            # Simplify action text (remove technical terms)
            simple_action = FarmerMessageGenerator._simplify_action_text(action.action)
            simple_reason = FarmerMessageGenerator._simplify_reason_text(action.reason)
            
            advice_list.append({
                "priority": action.priority,
                "action": simple_action,
                "reason": simple_reason
            })
        
        return advice_list
    
    @staticmethod
    def _convert_alert_type(alert_type: str) -> str:
        """Convert alert types to farmer-friendly names"""
        alert_mapping = {
            "HEAT_STRESS": "Heat Stress",
            "HEAVY_RAIN": "Heavy Rain",
            "DRY_SPELL": "Dry Spell",
            "HIGH_RAIN_PROBABILITY": "Rain Expected",
            "HIGH_WIND": "Strong Wind"
        }
        return alert_mapping.get(alert_type, alert_type.replace("_", " ").title())
    
    @staticmethod
    def _simplify_alert_message(message: str) -> str:
        """Simplify technical alert messages"""
        # Remove technical terms and simplify
        simplified = message
        
        # Replace technical terms
        replacements = {
            "may cause heat stress to crops and livestock": "can harm your crops and animals",
            "may cause waterlogging and soil erosion": "can flood fields and wash away soil",
            "expected for": "coming in",
            "consecutive days with minimal rainfall": "days with very little rain",
            "strong winds": "very strong winds",
            "may damage crops and affect spraying": "can damage crops and make spraying unsafe"
        }
        
        for technical, simple in replacements.items():
            simplified = simplified.replace(technical, simple)
        
        return simplified
    
    @staticmethod
    def _simplify_action_text(action: str) -> str:
        """Simplify action text to be more direct"""
        # Make actions more direct and simple
        simplified = action
        
        # Common simplifications
        replacements = {
            "Increase irrigation frequency during early morning or evening": "Water your fields in morning or evening",
            "Avoid field work during peak heat hours (11 AM - 3 PM)": "Stay out of fields during hottest hours (11 AM - 3 PM)",
            "Provide shade for young plants and livestock": "Give shade to young plants and animals",
            "Stop all irrigation immediately": "Stop watering your fields now",
            "Check and improve field drainage": "Clear drainage channels in fields",
            "Delay sowing and transplanting": "Wait before planting new seeds",
            "Postpone pesticide and fertilizer application": "Don't spray pesticides or fertilizers now",
            "Conserve water through mulching": "Cover soil with leaves or straw to save water",
            "Plan supplemental irrigation": "Arrange extra water for your crops",
            "Consider drought-resistant crops for next season": "Think about drought-resistant crops for next season",
            "Delay sowing if rain expected within 2-3 days": "Wait 2-3 days before planting if rain is coming",
            "Prepare covered storage for harvested crops": "Get covered storage ready for your harvest",
            "Check and repair farm equipment before rain": "Fix your tools and equipment before rain",
            "Postpone pesticide spraying": "Don't spray pesticides in strong wind",
            "Secure loose materials and protect young plants": "Tie down loose items and protect young plants"
        }
        
        for technical, simple in replacements.items():
            simplified = simplified.replace(technical, simple)
        
        return simplified
    
    @staticmethod
    def _simplify_reason_text(reason: str) -> str:
        """Simplify reason text to be more understandable"""
        simplified = reason
        
        # Common simplifications
        replacements = {
            "High temperatures increase water needs and prevent crop stress": "Crops need more water in hot weather",
            "Protect yourself and livestock from heat exhaustion": "Keep yourself and animals safe from heat",
            "Prevent heat damage and reduce stress": "Keep plants and animals cool",
            "Prevent waterlogging and root damage": "Too much water can damage crop roots",
            "Remove excess water and prevent soil erosion": "Clear extra water and protect soil from washing away",
            "Seeds may wash away and young plants may drown": "Rain can wash away seeds and flood young plants",
            "Rain will wash away chemicals and waste money": "Rain will waste your pesticides and fertilizers",
            "Reduce soil evaporation and maintain moisture": "Keep water in the soil longer",
            "Maintain crop water requirements during dry period": "Give crops enough water during dry times",
            "Prepare for future water scarcity": "Get ready for future water shortages",
            "Seeds need proper conditions to germinate": "Seeds need good weather to grow",
            "Protect harvest from unexpected rain damage": "Keep your harvest safe from rain",
            "Wet conditions make equipment maintenance difficult": "Hard to fix equipment when wet",
            "Wind causes spray drift and reduces effectiveness": "Wind blows pesticides away from crops",
            "Prevent damage from strong winds": "Keep crops safe from wind damage"
        }
        
        for technical, simple in replacements.items():
            simplified = simplified.replace(technical, simple)
        
        return simplified


# Convenience function for direct usage
def generate_farmer_message(weather_result: WeatherAlertOutput, location_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to generate farmer-friendly message
    
    Args:
        weather_result: Weather intelligence from agent
        location_info: Optional location details
        
    Returns:
        Farmer-friendly message structure
    """
    return FarmerMessageGenerator.generate_farmer_message(weather_result, location_info)
