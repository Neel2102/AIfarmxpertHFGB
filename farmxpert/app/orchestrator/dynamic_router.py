"""
Dynamic Router API
Endpoints for managing dynamic data and real-time monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response
from farmxpert.app.shared.services.dynamic_data_service import dynamic_data_service

router = APIRouter()

# In-memory store for monitored locations (in production, use Redis/Database)
MONITORED_LOCATIONS = [
    {
        "id": "ankleshwar_field_01",
        "latitude": 21.7051,
        "longitude": 72.9959,
        "district": "Ankleshwar",
        "state": "Gujarat",
        "crop_type": "cotton",
        "active": True,
        "added_at": "2026-02-03T00:00:00Z"
    }
]

@router.get("/locations")
async def get_monitored_locations():
    """Get all monitored locations"""
    return create_success_response(
        {
            "locations": MONITORED_LOCATIONS,
            "total_count": len(MONITORED_LOCATIONS),
            "active_count": len([loc for loc in MONITORED_LOCATIONS if loc.get("active", True)])
        },
        message="Monitored locations retrieved successfully"
    )

@router.post("/locations")
async def add_monitored_location(location_data: Dict[str, Any]):
    """Add a new location for monitoring"""
    try:
        required_fields = ["latitude", "longitude", "district", "state", "crop_type"]
        for field in required_fields:
            if field not in location_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required field: {field}"
                )
        
        # Generate unique ID
        location_id = f"{location_data['district'].lower()}_field_{len(MONITORED_LOCATIONS) + 1:02d}"
        
        new_location = {
            "id": location_id,
            "latitude": location_data["latitude"],
            "longitude": location_data["longitude"],
            "district": location_data["district"],
            "state": location_data["state"],
            "crop_type": location_data["crop_type"],
            "active": location_data.get("active", True),
            "added_at": datetime.now().isoformat()
        }
        
        MONITORED_LOCATIONS.append(new_location)
        
        logger.info(f"Added new monitoring location: {location_id}")
        
        return create_success_response(
            new_location,
            message="Location added for monitoring successfully"
        )
        
    except Exception as e:
        logger.error(f"Error adding location: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "LOCATION_ADD_ERROR",
                str(e),
                {"location_data": location_data}
            )
        )

@router.put("/locations/{location_id}")
async def update_monitored_location(location_id: str, update_data: Dict[str, Any]):
    """Update an existing monitored location"""
    try:
        location_index = None
        for i, loc in enumerate(MONITORED_LOCATIONS):
            if loc["id"] == location_id:
                location_index = i
                break
        
        if location_index is None:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    "LOCATION_NOT_FOUND",
                    f"Location with ID {location_id} not found"
                )
            )
        
        # Update the location
        MONITORED_LOCATIONS[location_index].update(update_data)
        MONITORED_LOCATIONS[location_index]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Updated monitoring location: {location_id}")
        
        return create_success_response(
            MONITORED_LOCATIONS[location_index],
            message="Location updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "LOCATION_UPDATE_ERROR",
                str(e),
                {"location_id": location_id, "update_data": update_data}
            )
        )

@router.delete("/locations/{location_id}")
async def delete_monitored_location(location_id: str):
    """Remove a location from monitoring"""
    try:
        location_index = None
        for i, loc in enumerate(MONITORED_LOCATIONS):
            if loc["id"] == location_id:
                location_index = i
                break
        
        if location_index is None:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    "LOCATION_NOT_FOUND",
                    f"Location with ID {location_id} not found"
                )
            )
        
        removed_location = MONITORED_LOCATIONS.pop(location_index)
        
        logger.info(f"Removed monitoring location: {location_id}")
        
        return create_success_response(
            removed_location,
            message="Location removed from monitoring successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing location: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "LOCATION_DELETE_ERROR",
                str(e),
                {"location_id": location_id}
            )
        )

@router.get("/data/soil/{location_id}")
async def get_dynamic_soil_data(location_id: str):
    """Get dynamic soil data for a specific location"""
    try:
        location = None
        for loc in MONITORED_LOCATIONS:
            if loc["id"] == location_id:
                location = loc
                break
        
        if location is None:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    "LOCATION_NOT_FOUND",
                    f"Location with ID {location_id} not found"
                )
            )
        
        soil_data = dynamic_data_service.get_dynamic_soil_data(location)
        
        return create_success_response(
            soil_data,
            message="Dynamic soil data retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching soil data: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "SOIL_DATA_ERROR",
                str(e),
                {"location_id": location_id}
            )
        )

@router.get("/data/crop/{location_id}")
async def get_dynamic_crop_data(location_id: str):
    """Get dynamic crop data for a specific location"""
    try:
        location = None
        for loc in MONITORED_LOCATIONS:
            if loc["id"] == location_id:
                location = loc
                break
        
        if location is None:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    "LOCATION_NOT_FOUND",
                    f"Location with ID {location_id} not found"
                )
            )
        
        crop_data = dynamic_data_service.get_dynamic_crop_data(
            location["crop_type"], 
            location
        )
        
        return create_success_response(
            crop_data,
            message="Dynamic crop data retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching crop data: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "CROP_DATA_ERROR",
                str(e),
                {"location_id": location_id}
            )
        )

@router.get("/data/irrigation/{location_id}")
async def get_dynamic_irrigation_data(location_id: str):
    """Get dynamic irrigation data for a specific location"""
    try:
        location = None
        for loc in MONITORED_LOCATIONS:
            if loc["id"] == location_id:
                location = loc
                break
        
        if location is None:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    "LOCATION_NOT_FOUND",
                    f"Location with ID {location_id} not found"
                )
            )
        
        # Get crop data first
        crop_data = dynamic_data_service.get_dynamic_crop_data(
            location["crop_type"], 
            location
        )
        
        irrigation_data = dynamic_data_service.get_dynamic_irrigation_data(
            location, 
            crop_data
        )
        
        return create_success_response(
            irrigation_data,
            message="Dynamic irrigation data retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching irrigation data: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "IRRIGATION_DATA_ERROR",
                str(e),
                {"location_id": location_id}
            )
        )

@router.get("/data/fertilizer/{location_id}")
async def get_dynamic_fertilizer_data(location_id: str):
    """Get dynamic fertilizer data for a specific location"""
    try:
        location = None
        for loc in MONITORED_LOCATIONS:
            if loc["id"] == location_id:
                location = loc
                break
        
        if location is None:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    "LOCATION_NOT_FOUND",
                    f"Location with ID {location_id} not found"
                )
            )
        
        # Get crop data first
        crop_data = dynamic_data_service.get_dynamic_crop_data(
            location["crop_type"], 
            location
        )
        
        fertilizer_data = dynamic_data_service.get_dynamic_fertilizer_data(
            location, 
            crop_data
        )
        
        return create_success_response(
            fertilizer_data,
            message="Dynamic fertilizer data retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fertilizer data: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "FERTILIZER_DATA_ERROR",
                str(e),
                {"location_id": location_id}
            )
        )

@router.get("/refresh/{location_id}")
async def refresh_all_data(location_id: str):
    """Force refresh all dynamic data for a location"""
    try:
        location = None
        for loc in MONITORED_LOCATIONS:
            if loc["id"] == location_id:
                location = loc
                break
        
        if location is None:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    "LOCATION_NOT_FOUND",
                    f"Location with ID {location_id} not found"
                )
            )
        
        # Clear cache for this location
        cache_keys_to_clear = [
            f"soil_{location['latitude']}_{location['longitude']}",
            f"crop_{location['crop_type']}_{location['latitude']}_{location['longitude']}",
            f"irrigation_{location['latitude']}_{location['longitude']}",
            f"fertilizer_{location['crop_type']}_{location['latitude']}_{location['longitude']}"
        ]
        
        for key in cache_keys_to_clear:
            if key in dynamic_data_service.cache:
                del dynamic_data_service.cache[key]
        
        # Fetch fresh data
        soil_data = dynamic_data_service.get_dynamic_soil_data(location)
        crop_data = dynamic_data_service.get_dynamic_crop_data(location["crop_type"], location)
        irrigation_data = dynamic_data_service.get_dynamic_irrigation_data(location, crop_data)
        fertilizer_data = dynamic_data_service.get_dynamic_fertilizer_data(location, crop_data)
        
        return create_success_response(
            {
                "location_id": location_id,
                "refresh_timestamp": datetime.now().isoformat(),
                "data": {
                    "soil": soil_data,
                    "crop": crop_data,
                    "irrigation": irrigation_data,
                    "fertilizer": fertilizer_data
                }
            },
            message="All dynamic data refreshed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                "REFRESH_ERROR",
                str(e),
                {"location_id": location_id}
            )
        )
