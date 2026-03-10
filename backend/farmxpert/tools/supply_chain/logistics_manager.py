from typing import Dict, Any, List, Optional, Tuple
import math
import logging

logger = logging.getLogger(__name__)

class LogisticsManagerTool:
    """
    Tool to manage logistics, calculate distances, and estimate transport costs.
    Parameters are hardcoded for local simulation but structured for API integration (e.g., OpenRouteService).
    """
    
    def calculate_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Dict[str, Any]:
        """
        Calculate distance and estimated time between two lat/lon points using Haversine formula.
        """
        try:
            distance_km = self._haversine_distance(origin[0], origin[1], destination[0], destination[1])
            
            # Estimate time (avg speed 40 km/h for farm transport)
            duration_hours = distance_km / 40.0
            
            # Estimate cost (approx ₹50 per km for small truck)
            estimated_cost = distance_km * 50
            
            return {
                "success": True,
                "distance_km": round(distance_km, 2),
                "duration_hours": round(duration_hours, 2),
                "estimated_cost_inr": round(estimated_cost, 2),
                "route_type": "Road (Simulated)"
            }
        except Exception as e:
            logger.error(f"Error calculating route: {e}")
            return {"success": False, "error": str(e)}

    def find_nearest_storage(self, farm_location: Tuple[float, float]) -> List[Dict[str, Any]]:
        """
        Find simulated storage facilities near the farm.
        """
        # Simulated database of cold storages in Gujarat region
        storages = [
            {"id": "st1", "name": "Amreli Cold Chain", "lat": 21.60, "lon": 71.22, "capacity": "5000 tons", "rate": "₹2/kg/month"},
            {"id": "st2", "name": "Rajkot Agro Storage", "lat": 22.30, "lon": 70.80, "capacity": "10000 tons", "rate": "₹2.5/kg/month"},
            {"id": "st3", "name": "Surat Fresh Hub", "lat": 21.17, "lon": 72.83, "capacity": "8000 tons", "rate": "₹3/kg/month"}
        ]
        
        results = []
        for st in storages:
            dist = self._haversine_distance(farm_location[0], farm_location[1], st["lat"], st["lon"])
            if dist < 200: # filter within 200km
                st["distance_km"] = round(dist, 2)
                results.append(st)
                
        return sorted(results, key=lambda x: x["distance_km"])

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # Convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lon2, lat1, lat2])

        # Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a)) 
        r = 6371 # Radius of earth in kilometers
        return c * r
