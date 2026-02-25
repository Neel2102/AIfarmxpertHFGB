import logging

from ..models.weather_summary_models import WeatherSummary
from ..models.output_models import (
    GrowthHealthStatus, GrowthAlert
)
from ..models.output_models import GrowthStageAssessment

logger = logging.getLogger(__name__)


class GrowthWeatherCorrelation:

    @staticmethod
    def correlate(
        stage: GrowthStageAssessment,
        health: GrowthHealthStatus,
        alerts: list[GrowthAlert],
        weather: WeatherSummary
    ) -> tuple[GrowthHealthStatus, list[GrowthAlert]]:

        # If growth already normal, no need to over-analyze
        if health.status == "NORMAL":
            return health, alerts

        # ---------------- HEAT STRESS ---------------- #
        if weather.heat_stress_days >= 3:
            logger.info("🌦️ Growth deviation likely due to heat stress")

            health.reason = (
                "Recent high temperatures may have slowed crop growth"
            )

            alerts.append(
                GrowthAlert(
                    alert_type="WEATHER_IMPACT",
                    severity="LOW",
                    confidence=0.6,
                    message="High temperatures in recent days can temporarily slow crop growth."
                )
            )
            
            # Display weather correlation in tabular format
            print(f"\n🌦️ WEATHER CORRELATION ANALYSIS")
            print(f"┌{'─'*20}┬{'─'*12}┬{'─'*20}┐")
            print(f"│{'Weather Factor':^20}│{'Value':^12}│{'Impact':^20}│")
            print(f"├{'─'*20}┼{'─'*12}┼{'─'*20}┤")
            print(f"│{'Heat Stress Days':^20}│{weather.heat_stress_days:^12}│{'High Stress':^20}│")
            print(f"│{'Avg Temperature':^20}│{weather.avg_temperature:.1f}°C{'':^8}│{'Above Optimal':^20}│")
            print(f"│{'Dry Days':^20}│{weather.dry_days:^12}│{'Moderate':^20}│")
            print(f"│{'Rainfall':^20}│{weather.total_rainfall_mm:.1f}mm{'':^7}│{'Insufficient':^20}│")
            print(f"└{'─'*20}┴{'─'*12}┴{'─'*20}┘")

            return health, alerts

        # ---------------- DROUGHT ---------------- #
        if weather.dry_days >= 5:
            logger.info("🌦️ Growth deviation likely due to dry conditions")

            health.reason = (
                "Limited rainfall in recent days may be affecting growth speed"
            )

            alerts.append(
                GrowthAlert(
                    alert_type="WEATHER_IMPACT",
                    severity="LOW",
                    confidence=0.65,
                    message="Dry weather conditions can slow plant development."
                )
            )

            return health, alerts

        # ---------------- EXCESS RAIN ---------------- #
        if weather.heavy_rain_days >= 3:
            logger.info("🌦️ Growth deviation likely due to excess rainfall")

            health.reason = (
                "Excess rainfall in recent days may have stressed the crop"
            )

            alerts.append(
                GrowthAlert(
                    alert_type="WEATHER_IMPACT",
                    severity="LOW",
                    confidence=0.6,
                    message="Excess rainfall can affect root health and growth rate."
                )
            )

            return health, alerts

        # ---------------- NO CLEAR WEATHER CAUSE ---------------- #
        logger.info("🌦️ No strong weather correlation found")

        return health, alerts
