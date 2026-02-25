from datetime import datetime
import logging

from ..models.input_models import GrowthMonitorInput
from ..models.output_models import (
    GrowthHealthStatus,
    GrowthAlert
)
from ..models.output_models import GrowthStageAssessment

logger = logging.getLogger(__name__)


class GrowthHealthEngine:

    @staticmethod
    def evaluate(
        input_data: GrowthMonitorInput,
        stage: GrowthStageAssessment
    ) -> tuple[GrowthHealthStatus, list[GrowthAlert]]:

        alerts: list[GrowthAlert] = []

        # ---------------- SAFETY CHECK ---------------- #
        if stage.current_stage in ["UNKNOWN", "OUT_OF_RANGE"]:
            logger.warning("Stage uncertain, skipping health judgement")

            return (
                GrowthHealthStatus(
                    status="UNKNOWN",
                    deviation_detected=False,
                    reason="Insufficient information to assess growth health"
                ),
                alerts
            )

        # ---------------- CONFIDENCE CHECK ---------------- #
        if stage.confidence < 0.5:
            logger.info("Low confidence stage estimation")

            return (
                GrowthHealthStatus(
                    status="UNCERTAIN",
                    deviation_detected=False,
                    reason="Growth stage confidence is low"
                ),
                alerts
            )

        # ---------------- TIME-BASED DEVIATION ---------------- #
        if stage.estimated_days_in_stage is not None:
            if stage.estimated_days_in_stage > GrowthHealthEngine._expected_days(stage.current_stage):
                logger.warning("🐢 Slow growth detected")

                alerts.append(
                    GrowthAlert(
                        alert_type="SLOW_GROWTH",
                        severity="MEDIUM",
                        confidence=0.7,
                        message=(
                            "Crop appears to be progressing slower than expected "
                            "for the current growth stage."
                        )
                    )
                )

                return (
                    GrowthHealthStatus(
                        status="SLOW",
                        deviation_detected=True,
                        reason="Crop has spent longer than expected in this stage"
                    ),
                    alerts
                )

        # ---------------- VISUAL QUALITY HEURISTIC ---------------- #
        if len(input_data.images) == 1:
            logger.info("📷 Limited visual input, reducing certainty")
            
            health_status = GrowthHealthStatus(
                status="NORMAL",
                deviation_detected=False,
                reason="Growth appears normal, but more images can improve accuracy"
            )
            
            # Display results in tabular format
            print(f"\n🏥 GROWTH HEALTH ASSESSMENT")
            print(f"┌{'─'*18}┬{'─'*15}┬{'─'*25}┐")
            print(f"│{'Metric':^18}│{'Status':^15}│{'Assessment':^25}│")
            print(f"├{'─'*18}┼{'─'*15}┼{'─'*25}┤")
            print(f"│{'Health Status':^18}│{health_status.status:^15}│{'Normal Growth':^25}│")
            print(f"│{'Deviation':^18}│{'No':^15}│{'Within Expected Range':^25}│")
            print(f"│{'Image Quality':^18}│{'Limited':^15}│{'Single Image Only':^25}│")
            print(f"│{'Confidence':^18}│{'Medium':^15}│{'More Images Needed':^25}│")
            print(f"└{'─'*18}┴{'─'*15}┴{'─'*25}┘")

            return (health_status, alerts)

        # ---------------- NORMAL CASE ---------------- #
        logger.info("Growth appears normal")

        return (
            GrowthHealthStatus(
                status="NORMAL",
                deviation_detected=False,
                reason="Growth is progressing within expected range"
            ),
            alerts
        )

    # ---------------- UTIL ---------------- #

    @staticmethod
    def _expected_days(stage_name: str) -> int:
        """
        Approximate expected days per stage (V1 heuristic)
        """
        return {
            "Germination": 7,
            "Vegetative": 35,
            "Flowering": 30,
            "Boll Formation": 40,
            "Maturity": 50
        }.get(stage_name, 30)
