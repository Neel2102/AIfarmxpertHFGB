"""
Weather Alert Thresholds
Defines the threshold values for weather alerts
"""

# Temperature thresholds (in Celsius)
HEAT_STRESS_TEMP = 35.0
COLD_STRESS_TEMP = 5.0

# Rainfall thresholds (in mm)
HEAVY_RAIN_MM = 10.0
LIGHT_RAIN_MM = 0.1
DRY_SPELL_RAIN_MM = 2.0  # Less than this is considered dry

# Dry spell detection
CONSECUTIVE_DRY_DAYS = 3  # Number of consecutive dry days for alert

# Rainfall probability thresholds
HIGH_RAIN_PROBABILITY = 0.7  # 70% or higher
LOW_RAIN_PROBABILITY = 0.2   # 20% or lower

# Wind thresholds (in km/h)
HIGH_WIND_KMH = 50.0

# Alert timing
ALERT_COOLDOWN_MINUTES = 30

# Humidity thresholds
HIGH_HUMIDITY = 80.0
LOW_HUMIDITY = 30.0

# Visibility thresholds
LOW_VISIBILITY_KM = 1.0
