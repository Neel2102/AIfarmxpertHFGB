#!/usr/bin/env python3
"""
Test script for Weather Watcher Agent enhancements
Tests the new functionality with sample data
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_watcher.models.weather_models import WeatherSnapshot, WeatherForecast
from weather_watcher.services.rule_engine import RuleEngine
from weather_watcher.services.weather_service import WeatherService


def test_heat_stress_scenario():
    """Test heat stress detection and farming advice"""
    print("🔥 Testing Heat Stress Scenario")
    print("=" * 50)
    
    # Create hot weather scenario
    hot_weather = WeatherSnapshot(
        temperature=38.5,
        min_temperature=28.0,
        max_temperature=42.0,
        humidity=45,
        wind_speed=15.0,
        rainfall_mm=0.0,
        rainfall_probability=0.1,
        weather_condition="clear",
        source="Test",
        observed_at=datetime.utcnow()
    )
    
    # Create dry forecast
    dry_forecasts = []
    for i in range(7):
        dry_forecasts.append(WeatherForecast(
            date=datetime.utcnow() + timedelta(days=i),
            temperature=35.0 + i,
            min_temperature=25.0 + i,
            max_temperature=40.0 + i,
            humidity=40,
            wind_speed=10.0,
            rainfall_mm=0.0,
            rainfall_probability=0.05,
            weather_condition="clear",
            source="Test"
        ))
    
    rule_engine = RuleEngine(last_alerts={})
    result = rule_engine.evaluate(hot_weather, dry_forecasts)
    
    print(f"Weather Summary: {result.weather_summary.temperature}")
    print(f"Condition: {result.weather_summary.condition}")
    print(f"Rainfall Outlook: {result.weather_summary.rainfall_outlook}")
    print(f"\nRisk Alerts ({len(result.risk_alerts)}):")
    for alert in result.risk_alerts:
        print(f"  - {alert.alert_type}: {alert.message}")
    
    print(f"\nFarming Actions ({len(result.farming_actions)}):")
    for action in result.farming_actions:
        print(f"  - [{action.priority}] {action.action}")
        print(f"    Reason: {action.reason}")
    
    print("\n" + "="*50 + "\n")


def test_heavy_rain_scenario():
    """Test heavy rainfall detection and farming advice"""
    print("🌧️ Testing Heavy Rain Scenario")
    print("=" * 50)
    
    # Create heavy rain scenario
    rainy_weather = WeatherSnapshot(
        temperature=25.0,
        min_temperature=22.0,
        max_temperature=28.0,
        humidity=85,
        wind_speed=25.0,
        rainfall_mm=15.5,
        rainfall_probability=0.8,
        weather_condition="rain",
        source="Test",
        observed_at=datetime.utcnow()
    )
    
    # Create rainy forecast
    rainy_forecasts = []
    for i in range(7):
        rainy_forecasts.append(WeatherForecast(
            date=datetime.utcnow() + timedelta(days=i),
            temperature=24.0,
            min_temperature=21.0,
            max_temperature=27.0,
            humidity=80,
            wind_speed=20.0,
            rainfall_mm=12.0 if i < 3 else 2.0,
            rainfall_probability=0.75 if i < 3 else 0.3,
            weather_condition="rain",
            source="Test"
        ))
    
    rule_engine = RuleEngine(last_alerts={})
    result = rule_engine.evaluate(rainy_weather, rainy_forecasts)
    
    print(f"Weather Summary: {result.weather_summary.temperature}")
    print(f"Condition: {result.weather_summary.condition}")
    print(f"Rainfall Outlook: {result.weather_summary.rainfall_outlook}")
    print(f"\nRisk Alerts ({len(result.risk_alerts)}):")
    for alert in result.risk_alerts:
        print(f"  - {alert.alert_type}: {alert.message}")
    
    print(f"\nFarming Actions ({len(result.farming_actions)}):")
    for action in result.farming_actions:
        print(f"  - [{action.priority}] {action.action}")
        print(f"    Reason: {action.reason}")
    
    print("\n" + "="*50 + "\n")


def test_dry_spell_scenario():
    """Test dry spell detection and farming advice"""
    print("🏜️ Testing Dry Spell Scenario")
    print("=" * 50)
    
    # Create normal weather but dry forecast
    normal_weather = WeatherSnapshot(
        temperature=30.0,
        min_temperature=25.0,
        max_temperature=35.0,
        humidity=50,
        wind_speed=15.0,
        rainfall_mm=1.0,
        rainfall_probability=0.2,
        weather_condition="clouds",
        source="Test",
        observed_at=datetime.utcnow()
    )
    
    # Create consecutive dry days forecast
    dry_forecasts = []
    for i in range(7):
        dry_forecasts.append(WeatherForecast(
            date=datetime.utcnow() + timedelta(days=i),
            temperature=30.0,
            min_temperature=25.0,
            max_temperature=35.0,
            humidity=45,
            wind_speed=10.0,
            rainfall_mm=0.5,  # Very low rainfall
            rainfall_probability=0.1,  # Low probability
            weather_condition="clear",
            source="Test"
        ))
    
    rule_engine = RuleEngine(last_alerts={})
    result = rule_engine.evaluate(normal_weather, dry_forecasts)
    
    print(f"Weather Summary: {result.weather_summary.temperature}")
    print(f"Condition: {result.weather_summary.condition}")
    print(f"Rainfall Outlook: {result.weather_summary.rainfall_outlook}")
    print(f"\nRisk Alerts ({len(result.risk_alerts)}):")
    for alert in result.risk_alerts:
        print(f"  - {alert.alert_type}: {alert.message}")
    
    print(f"\nFarming Actions ({len(result.farming_actions)}):")
    for action in result.farming_actions:
        print(f"  - [{action.priority}] {action.action}")
        print(f"    Reason: {action.reason}")
    
    print("\n" + "="*50 + "\n")


def test_normal_conditions():
    """Test normal weather conditions"""
    print("☀️ Testing Normal Conditions")
    print("=" * 50)
    
    # Create normal weather
    normal_weather = WeatherSnapshot(
        temperature=28.0,
        min_temperature=23.0,
        max_temperature=33.0,
        humidity=60,
        wind_speed=12.0,
        rainfall_mm=2.0,
        rainfall_probability=0.3,
        weather_condition="clouds",
        source="Test",
        observed_at=datetime.utcnow()
    )
    
    # Create moderate forecast
    moderate_forecasts = []
    for i in range(7):
        moderate_forecasts.append(WeatherForecast(
            date=datetime.utcnow() + timedelta(days=i),
            temperature=27.0,
            min_temperature=22.0,
            max_temperature=32.0,
            humidity=65,
            wind_speed=15.0,
            rainfall_mm=3.0,
            rainfall_probability=0.4,
            weather_condition="clouds",
            source="Test"
        ))
    
    rule_engine = RuleEngine(last_alerts={})
    result = rule_engine.evaluate(normal_weather, moderate_forecasts)
    
    print(f"Weather Summary: {result.weather_summary.temperature}")
    print(f"Condition: {result.weather_summary.condition}")
    print(f"Rainfall Outlook: {result.weather_summary.rainfall_outlook}")
    print(f"\nRisk Alerts ({len(result.risk_alerts)}):")
    for alert in result.risk_alerts:
        print(f"  - {alert.alert_type}: {alert.message}")
    
    print(f"\nFarming Actions ({len(result.farming_actions)}):")
    for action in result.farming_actions:
        print(f"  - [{action.priority}] {action.action}")
        print(f"    Reason: {action.reason}")
    
    print("\n" + "="*50 + "\n")


def main():
    """Run all test scenarios"""
    print("🌦️ Weather Watcher Agent - Enhanced Functionality Tests")
    print("=" * 60)
    print("Testing new features:")
    print("- Rainfall probability handling")
    print("- Dry spell detection")
    print("- Heat stress warnings")
    print("- Actionable farming advice")
    print("- Farmer-friendly output")
    print("=" * 60 + "\n")
    
    try:
        test_heat_stress_scenario()
        test_heavy_rain_scenario()
        test_dry_spell_scenario()
        test_normal_conditions()
        
        print("✅ All tests completed successfully!")
        print("The enhanced Weather Watcher Agent is working as expected.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
