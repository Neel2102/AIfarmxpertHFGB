from datetime import datetime
import logging
from typing import Optional

from ..models.input_models import GrowthMonitorInput
from ..models.output_models import GrowthStageAssessment
from ..constraints.growth_timelines import CROP_GROWTH_TIMELINES

logger = logging.getLogger(__name__)


class GrowthStageEngine:

    @staticmethod
    def estimate_stage(input_data: GrowthMonitorInput) -> GrowthStageAssessment:
        crop_name = input_data.crop.crop_name.lower()
        sowing_date = input_data.crop.sowing_date

        # Case 1: Missing sowing date
        if not sowing_date:
            logger.warning("Sowing date missing, cannot estimate stage reliably")
            return GrowthStageAssessment(
                current_stage="UNKNOWN",
                confidence=0.3,
                estimated_days_in_stage=None
            )

        # Case 2: Crop not supported
        if crop_name not in CROP_GROWTH_TIMELINES:
            logger.warning(f"Crop timeline not found for {crop_name}")
            return GrowthStageAssessment(
                current_stage="UNKNOWN",
                confidence=0.4,
                estimated_days_in_stage=None
            )

        days_since_sowing = (input_data.triggered_at - sowing_date).days
        timeline = CROP_GROWTH_TIMELINES[crop_name]

        for stage_name, start_day, end_day in timeline:
            if start_day <= days_since_sowing <= end_day:
                estimated_days = days_since_sowing - start_day

                confidence = GrowthStageEngine._calculate_confidence(
                    days_since_sowing,
                    start_day,
                    end_day,
                    input_data.images
                )

                logger.info(f"Estimated stage: {stage_name}")
                
                # Display results in tabular format
                print(f"\n📊 GROWTH STAGE ASSESSMENT")
                print(f"┌{'─'*20}┬{'─'*15}┬{'─'*20}┐")
                print(f"│{'Parameter':^20}│{'Value':^15}│{'Details':^20}│")
                print(f"├{'─'*20}┼{'─'*15}┼{'─'*20}┤")
                print(f"│{'Crop Type':^20}│{crop_name.upper():^15}│{'':^20}│")
                print(f"│{'Days Since Sowing':^20}│{days_since_sowing:^15}│{'':^20}│")
                print(f"│{'Current Stage':^20}│{stage_name:^15}│{'':^20}│")
                print(f"│{'Confidence':^20}│{confidence:.2f}{'':^12}│{'High' if confidence > 0.8 else 'Medium' if confidence > 0.5 else 'Low':^20}│")
                print(f"│{'Days in Stage':^20}│{estimated_days:^15}│{'':^20}│")
                print(f"└{'─'*20}┴{'─'*15}┴{'─'*20}┘")

                return GrowthStageAssessment(
                    current_stage=stage_name,
                    confidence=confidence,
                    estimated_days_in_stage=estimated_days
                )

        # Case 3: Out of known range
        logger.warning("🌱 Crop appears outside known growth timeline")
        return GrowthStageAssessment(
            current_stage="OUT_OF_RANGE",
            confidence=0.5,
            estimated_days_in_stage=None
        )

    # ---------------- UTIL ---------------- #

    @staticmethod
    def _calculate_confidence(
        days: int,
        start: int,
        end: int,
        images: list
    ) -> float:
        """
        Confidence increases if:
        - Days are well inside range
        - Valid images are present
        """

        range_size = end - start
        center = (start + end) / 2

        distance_from_center = abs(days - center)
        base_confidence = 1 - (distance_from_center / range_size)

        # Image bonus (V1 heuristic)
        image_bonus = 0.1 if images else 0.0

        confidence = min(0.95, base_confidence + image_bonus)
        return round(max(confidence, 0.4), 2)
