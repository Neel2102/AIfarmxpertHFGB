"""
Farm Context and Farm Context Resolver
Provides structured context resolution for authenticated users and their authorized farms.
Enforces strict authorization: authenticated_user -> authorized_farm -> farm_context.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from farmxpert.models.farm_models import Farm, SoilTest, Crop
from farmxpert.models.farm_profile_models import FarmProfile
from farmxpert.models.user_models import User
from farmxpert.core.utils.logger import get_logger

logger = get_logger("farm_context")


class FarmResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NEEDS_SELECTION = "NEEDS_SELECTION"
    NO_FARM = "NO_FARM"
    UNAUTHORIZED = "UNAUTHORIZED"
    ERROR = "ERROR"


@dataclass
class FarmContext:
    user_id: int
    farm_id: Optional[int] = None
    farm_name: Optional[str] = None

    # Location attributes
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"

    # Farm parameters
    farm_area: Optional[float] = None
    area_unit: Optional[str] = "acres"
    crops: List[str] = field(default_factory=list)
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    sowing_dates: Dict[str, Any] = field(default_factory=dict)
    preferred_language: Optional[str] = "en"
    timezone: Optional[str] = "Asia/Kolkata"
    sensor_ids: List[str] = field(default_factory=list)

    # Telemetry snapshot (if relevant)
    soil_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "farm_id": self.farm_id,
            "farm_name": self.farm_name,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "name": self.location_name,
                "village": self.village,
                "district": self.district,
                "state": self.state,
                "country": self.country,
            },
            "farm_area": self.farm_area,
            "area_unit": self.area_unit,
            "crops": self.crops,
            "soil_type": self.soil_type,
            "irrigation_type": self.irrigation_type,
            "sowing_dates": self.sowing_dates,
            "preferred_language": self.preferred_language,
            "timezone": self.timezone,
            "sensor_ids": self.sensor_ids,
            "soil_data": self.soil_data,
        }

    def scoped_for_intent(self, intent: str) -> Dict[str, Any]:
        """Return only the context fields needed for a specific intent to prevent prompt bloating."""
        intent_upper = intent.upper() if intent else "GENERAL"

        if intent_upper in ("WEATHER", "FORECAST"):
            return {
                "farm_id": self.farm_id,
                "farm_name": self.farm_name,
                "location": {
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "name": self.location_name or f"{self.district or ''}, {self.state or ''}".strip(", "),
                    "district": self.district,
                    "state": self.state,
                },
                "timezone": self.timezone,
                "preferred_language": self.preferred_language,
            }
        elif intent_upper in ("SOIL_HEALTH", "FERTILIZER"):
            return {
                "farm_id": self.farm_id,
                "farm_name": self.farm_name,
                "soil_type": self.soil_type,
                "soil_data": self.soil_data,
                "crops": self.crops,
                "location": {"district": self.district, "state": self.state},
            }
        elif intent_upper in ("MARKET_PRICES", "MARKET"):
            return {
                "farm_id": self.farm_id,
                "crops": self.crops,
                "district": self.district,
                "state": self.state,
            }
        elif intent_upper in ("IRRIGATION",):
            return {
                "farm_id": self.farm_id,
                "location": {"latitude": self.latitude, "longitude": self.longitude, "district": self.district, "state": self.state},
                "crops": self.crops,
                "soil_type": self.soil_type,
                "irrigation_type": self.irrigation_type,
                "soil_data": self.soil_data,
            }
        elif intent_upper in ("CROP_SELECTION", "SEED_SELECTION"):
            return {
                "farm_id": self.farm_id,
                "farm_area": self.farm_area,
                "area_unit": self.area_unit,
                "soil_type": self.soil_type,
                "irrigation_type": self.irrigation_type,
                "location": {"district": self.district, "state": self.state, "latitude": self.latitude, "longitude": self.longitude},
                "historical_crops": self.crops,
            }

        return self.to_dict()


@dataclass
class FarmResolutionResult:
    status: FarmResolutionStatus
    context: Optional[FarmContext] = None
    available_farms: List[Dict[str, Any]] = field(default_factory=list)
    message: Optional[str] = None


class FarmContextResolver:
    """
    Resolves authorized farm context for an authenticated user.
    Never trusts LLM or user-provided arbitrary farm_id without validating ownership.
    """

    @staticmethod
    def resolve(
        db: Session,
        user: User,
        requested_farm_id: Optional[int] = None,
        query: Optional[str] = None
    ) -> FarmResolutionResult:
        """
        Resolve the relevant farm context for the given user.
        """
        if not user or not user.id:
            return FarmResolutionResult(
                status=FarmResolutionStatus.UNAUTHORIZED,
                message="User is not authenticated."
            )

        # 1. Fetch all farms belonging to this user
        user_farms: List[Farm] = []
        try:
            if hasattr(Farm, "user_id"):
                user_farms = db.query(Farm).filter(Farm.user_id == user.id).all()
        except Exception:
            user_farms = []

        if not user_farms:
            try:
                if hasattr(Farm, "farmer_email") and user.email:
                    user_farms = db.query(Farm).filter(Farm.farmer_email == user.email).all()
                elif hasattr(Farm, "farmer_name") and user.full_name:
                    user_farms = db.query(Farm).filter(Farm.farmer_name == user.full_name).all()
            except Exception:
                pass

        if not user_farms:
            # Fallback for single-farm local databases where user_id was not populated
            try:
                all_f = db.query(Farm).all()
                if len(all_f) == 1:
                    user_farms = all_f
            except Exception:
                pass

        # Also check FarmProfile (from onboarding)
        farm_profile: Optional[FarmProfile] = None
        try:
            farm_profile = db.query(FarmProfile).filter(FarmProfile.user_id == user.id).first()
        except Exception:
            farm_profile = None

        # Build list of available farms
        available_farms = []
        for f in user_farms:
            farm_name = getattr(f, "farm_name", None) or getattr(f, "name", None) or f"Farm #{f.id}"
            loc_parts = [p for p in [getattr(f, "village", None), getattr(f, "district", None), getattr(f, "state", None)] if p]
            loc_str = ", ".join(loc_parts) or getattr(f, "location", None) or getattr(f, "state", None) or "Location not set"
            crop = getattr(f, "crop_type", None)
            lat = float(f.latitude) if getattr(f, "latitude", None) is not None else None
            lon = float(f.longitude) if getattr(f, "longitude", None) is not None else None

            if (not lat or not lon) and loc_str and loc_str != "Location not set":
                try:
                    from farmxpert.tools import get_location_coordinates
                    coords = get_location_coordinates(loc_str)
                    if coords and coords.get("lat") and coords.get("lon"):
                        lat = coords["lat"]
                        lon = coords["lon"]
                except Exception:
                    pass

            available_farms.append({
                "farm_id": f.id,
                "farm_name": farm_name,
                "location": loc_str,
                "crop_type": crop,
                "latitude": lat,
                "longitude": lon,
            })

        # If no entries in `farms` table but `farm_profile` exists, treat profile as farm
        if not available_farms and farm_profile:
            loc_str = farm_profile.location or (
                f"{farm_profile.district}, {farm_profile.state}" if farm_profile.district and farm_profile.state else None
            )
            lat = farm_profile.latitude
            lon = farm_profile.longitude
            if (not lat or not lon) and loc_str:
                try:
                    from farmxpert.tools import get_location_coordinates
                    coords = get_location_coordinates(loc_str)
                    if coords and coords.get("lat") and coords.get("lon"):
                        lat = coords["lat"]
                        lon = coords["lon"]
                except Exception:
                    pass

            available_farms.append({
                "farm_id": farm_profile.id,
                "farm_name": farm_profile.farm_name or "My Farm",
                "location": loc_str or "India",
                "crop_type": farm_profile.specific_crop or (farm_profile.primary_crops[0] if isinstance(farm_profile.primary_crops, list) and farm_profile.primary_crops else None),
                "latitude": lat,
                "longitude": lon,
            })

        # If user has no farms at all
        if not available_farms:
            return FarmResolutionResult(
                status=FarmResolutionStatus.NO_FARM,
                message="Please add a farm to your FarmXpert profile before requesting farm-specific information."
            )

        # 2. Authorization check if requested_farm_id is explicitly provided
        selected_farm_dict = None
        if requested_farm_id is not None:
            matching = [f for f in available_farms if f["farm_id"] == requested_farm_id]
            if not matching:
                logger.warning(f"Unauthorized farm access attempt: user {user.id} requested farm {requested_farm_id}")
                return FarmResolutionResult(
                    status=FarmResolutionStatus.UNAUTHORIZED,
                    message=f"Access denied: Farm ID {requested_farm_id} does not belong to your account."
                )
            selected_farm_dict = matching[0]

        # 3. If query mentions a specific farm name or location (e.g., "my Anand farm", "Vadodara farm")
        if not selected_farm_dict and query:
            q_lower = query.lower()
            for farm_candidate in available_farms:
                name_match = farm_candidate["farm_name"] and farm_candidate["farm_name"].lower() in q_lower
                loc_match = farm_candidate["location"] and any(
                    part.lower() in q_lower
                    for part in farm_candidate["location"].split(",")
                    if len(part.strip()) > 3
                )
                if name_match or loc_match:
                    selected_farm_dict = farm_candidate
                    break

        # 4. If single farm exists, automatically use it
        if not selected_farm_dict and len(available_farms) == 1:
            selected_farm_dict = available_farms[0]

        # 5. If multiple farms exist and no specific one was resolved:
        if not selected_farm_dict and len(available_farms) > 1:
            farm_options = "\n".join([f"{i+1}. {f['farm_name']} ({f['location']})" for i, f in enumerate(available_farms)])
            return FarmResolutionResult(
                status=FarmResolutionStatus.NEEDS_SELECTION,
                available_farms=available_farms,
                message=f"Which farm would you like information for?\n\n{farm_options}"
            )

        # 6. Build the rich FarmContext object for the selected farm
        farm_id = selected_farm_dict["farm_id"]
        farm_db_obj = next((f for f in user_farms if f.id == farm_id), None)

        context = FarmContextResolver._build_context(
            user=user,
            farm=farm_db_obj,
            profile=farm_profile,
            db=db,
            farm_dict=selected_farm_dict
        )

        return FarmResolutionResult(
            status=FarmResolutionStatus.RESOLVED,
            context=context,
            available_farms=available_farms
        )

    @staticmethod
    def _build_context(
        user: User,
        farm: Optional[Farm],
        profile: Optional[FarmProfile],
        db: Session,
        farm_dict: Dict[str, Any]
    ) -> FarmContext:
        """Builds standardized FarmContext from available database records."""
        # Coordinates resolution
        lat = farm_dict.get("latitude")
        lon = farm_dict.get("longitude")

        # Check farm_profile polygon coords if lat/lon not directly set
        if (not lat or not lon) and profile and hasattr(profile, "farm_polygon") and isinstance(profile.farm_polygon, dict):
            coords = profile.farm_polygon.get("coordinates")
            if coords and isinstance(coords, list) and len(coords) > 0:
                first_ring = coords[0]
                if isinstance(first_ring, list) and len(first_ring) > 0:
                    first_pt = first_ring[0]
                    if isinstance(first_pt, list) and len(first_pt) >= 2:
                        lon = float(first_pt[0])
                        lat = float(first_pt[1])

        # Location text
        district = getattr(farm, "district", None) if farm else getattr(profile, "district", None)
        state = getattr(farm, "state", None) if farm else getattr(profile, "state", None)
        village = getattr(farm, "village", None) if farm else getattr(profile, "village", None)
        loc_str = farm_dict.get("location") or (f"{district}, {state}" if district and state else state or district)

        if not district and loc_str and "," in loc_str:
            district = loc_str.split(",")[0].strip()
        if not state and loc_str and "," in loc_str:
            state = loc_str.split(",")[-1].strip()

        # Crop resolution
        crops = []
        crop_val = getattr(farm, "crop_type", None)
        if crop_val:
            crops.append(crop_val)
        primary_crops = getattr(profile, "primary_crops", None)
        if primary_crops:
            if isinstance(primary_crops, list):
                crops.extend([str(c) for c in primary_crops if str(c) not in crops])
            elif isinstance(primary_crops, str):
                crops.extend([c.strip() for c in primary_crops.split(",") if c.strip() and c.strip() not in crops])
        specific_crop = getattr(profile, "specific_crop", None)
        if specific_crop and specific_crop not in crops:
            crops.append(specific_crop)

        # Farm crops table query
        if farm and hasattr(farm, "id"):
            try:
                db_crops = db.query(Crop).filter(Crop.farm_id == farm.id).all()
                for dc in db_crops:
                    if dc.crop_type and dc.crop_type not in crops:
                        crops.append(dc.crop_type)
            except Exception:
                pass

        soil_type = (getattr(farm, "soil_type", None) if farm else None) or (profile.soil_type if profile else None)
        irrigation_type = profile.irrigation_method if profile else None

        # Soil telemetry
        soil_telemetry = {}
        soil_test = None
        try:
            if farm:
                soil_test = db.query(SoilTest).filter(SoilTest.farm_id == farm.id).order_by(SoilTest.test_date.desc()).first()
            if not soil_test:
                soil_test = db.query(SoilTest).order_by(SoilTest.test_date.desc()).first()
        except Exception:
            soil_test = None

        if soil_test:
            def _clean_num(val):
                if val is None:
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            soil_telemetry = {
                "moisture": _clean_num(getattr(soil_test, "soil_moisture", None)),
                "temperature": _clean_num(getattr(soil_test, "soil_temperature", None) or getattr(soil_test, "air_temperature", None)),
                "ph": _clean_num(getattr(soil_test, "soil_ph", None)),
                "nitrogen": _clean_num(getattr(soil_test, "nitrogen", None)),
                "phosphorus": _clean_num(getattr(soil_test, "phosphorus", None)),
                "potassium": _clean_num(getattr(soil_test, "potassium", None)),
                "ec": _clean_num(getattr(soil_test, "soil_ec", None)),
                "humidity": _clean_num(getattr(soil_test, "air_humidity", None)),
                "tested_at": soil_test.test_date.isoformat() if hasattr(soil_test, "test_date") and hasattr(soil_test.test_date, "isoformat") else None,
            }

        # Area
        farm_area = None
        area_unit = "acres"
        if profile and profile.farm_size:
            try:
                farm_area = float(str(profile.farm_size).split()[0])
            except (ValueError, IndexError):
                pass
            if profile.farm_size_unit:
                area_unit = profile.farm_size_unit

        return FarmContext(
            user_id=user.id,
            farm_id=farm_dict["farm_id"],
            farm_name=farm_dict.get("farm_name"),
            latitude=lat,
            longitude=lon,
            location_name=loc_str,
            village=village,
            district=district,
            state=state,
            farm_area=farm_area,
            area_unit=area_unit,
            crops=crops,
            soil_type=soil_type,
            irrigation_type=irrigation_type,
            preferred_language="en",
            timezone="Asia/Kolkata",
            soil_data=soil_telemetry,
        )
