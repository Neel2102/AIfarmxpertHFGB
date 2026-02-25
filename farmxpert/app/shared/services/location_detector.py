"""
Location Detection Service for FarmXpert
Extracts location information from user queries and maps to coordinates
"""

import re
from typing import Dict, Optional, Tuple

# Major Indian cities with their coordinates
INDIAN_CITIES = {
    "ahmedabad": {"latitude": 23.0225, "longitude": 72.5714, "state": "Gujarat"},
    "bangalore": {"latitude": 12.9716, "longitude": 77.5946, "state": "Karnataka"},
    "bengaluru": {"latitude": 12.9716, "longitude": 77.5946, "state": "Karnataka"},
    "mumbai": {"latitude": 19.0760, "longitude": 72.8777, "state": "Maharashtra"},
    "delhi": {"latitude": 28.6139, "longitude": 77.2090, "state": "Delhi"},
    "new delhi": {"latitude": 28.6139, "longitude": 77.2090, "state": "Delhi"},
    "kolkata": {"latitude": 22.5726, "longitude": 88.3639, "state": "West Bengal"},
    "chennai": {"latitude": 13.0827, "longitude": 80.2707, "state": "Tamil Nadu"},
    "hyderabad": {"latitude": 17.3850, "longitude": 78.4867, "state": "Telangana"},
    "pune": {"latitude": 18.5204, "longitude": 73.8567, "state": "Maharashtra"},
    "jaipur": {"latitude": 26.9124, "longitude": 75.7873, "state": "Rajasthan"},
    "lucknow": {"latitude": 26.8467, "longitude": 80.9462, "state": "Uttar Pradesh"},
    "kanpur": {"latitude": 26.4499, "longitude": 80.3319, "state": "Uttar Pradesh"},
    "nagpur": {"latitude": 21.1458, "longitude": 79.0882, "state": "Maharashtra"},
    "indore": {"latitude": 22.7196, "longitude": 75.8577, "state": "Madhya Pradesh"},
    "thane": {"latitude": 19.2183, "longitude": 72.9781, "state": "Maharashtra"},
    "bhopal": {"latitude": 23.2599, "longitude": 77.4126, "state": "Madhya Pradesh"},
    "visakhapatnam": {"latitude": 17.6868, "longitude": 83.2185, "state": "Andhra Pradesh"},
    "pimpri": {"latitude": 18.6298, "longitude": 73.8078, "state": "Maharashtra"},
    "patna": {"latitude": 25.5941, "longitude": 85.1376, "state": "Bihar"},
    "vadodara": {"latitude": 22.3072, "longitude": 73.1812, "state": "Gujarat"},
    "ghaziabad": {"latitude": 28.6692, "longitude": 77.4538, "state": "Uttar Pradesh"},
    "ludhiana": {"latitude": 30.9010, "longitude": 75.8573, "state": "Punjab"},
    "agra": {"latitude": 27.1767, "longitude": 78.0081, "state": "Uttar Pradesh"},
    "nashik": {"latitude": 19.9975, "longitude": 73.7898, "state": "Maharashtra"},
    "faridabad": {"latitude": 28.4089, "longitude": 77.3178, "state": "Haryana"},
    "meerut": {"latitude": 28.9845, "longitude": 77.7064, "state": "Uttar Pradesh"},
    "rajkot": {"latitude": 22.3039, "longitude": 70.8022, "state": "Gujarat"},
    "kalyan": {"latitude": 19.2403, "longitude": 73.1305, "state": "Maharashtra"},
    "vasai": {"latitude": 19.4912, "longitude": 72.8398, "state": "Maharashtra"},
    "varanasi": {"latitude": 25.3176, "longitude": 82.9739, "state": "Uttar Pradesh"},
    "srinagar": {"latitude": 34.0837, "longitude": 74.7973, "state": "Jammu & Kashmir"},
    "dhanbad": {"latitude": 23.7957, "longitude": 86.4304, "state": "Jharkhand"},
    "jodhpur": {"latitude": 26.2389, "longitude": 73.0243, "state": "Rajasthan"},
    "amritsar": {"latitude": 31.6340, "longitude": 74.8723, "state": "Punjab"},
    "raipur": {"latitude": 21.2514, "longitude": 81.6296, "state": "Chhattisgarh"},
    "allahabad": {"latitude": 25.4358, "longitude": 81.8463, "state": "Uttar Pradesh"},
    "coimbatore": {"latitude": 11.0168, "longitude": 76.9558, "state": "Tamil Nadu"},
    "jabalpur": {"latitude": 23.1815, "longitude": 79.9864, "state": "Madhya Pradesh"},
    "gwalior": {"latitude": 26.2124, "longitude": 78.1772, "state": "Madhya Pradesh"},
    "vijayawada": {"latitude": 16.5062, "longitude": 80.6480, "state": "Andhra Pradesh"},
    "madurai": {"latitude": 9.9252, "longitude": 78.1198, "state": "Tamil Nadu"},
    "guwahati": {"latitude": 26.1445, "longitude": 91.7362, "state": "Assam"},
    "chandigarh": {"latitude": 30.7333, "longitude": 76.7794, "state": "Punjab"},
    "hubli": {"latitude": 15.3647, "longitude": 75.1240, "state": "Karnataka"},
    "mangalore": {"latitude": 12.9141, "longitude": 74.8560, "state": "Karnataka"},
    "erode": {"latitude": 11.3410, "longitude": 77.7182, "state": "Tamil Nadu"},
    "tiruchirappalli": {"latitude": 10.7905, "longitude": 78.7047, "state": "Tamil Nadu"},
    "salem": {"latitude": 11.6645, "longitude": 78.1460, "state": "Tamil Nadu"},
    "tirupur": {"latitude": 11.1085, "longitude": 77.3411, "state": "Tamil Nadu"},
    "guntur": {"latitude": 16.3067, "longitude": 80.4365, "state": "Andhra Pradesh"},
    "nellore": {"latitude": 14.4426, "longitude": 79.9865, "state": "Andhra Pradesh"},
    "thrissur": {"latitude": 10.5276, "longitude": 76.2144, "state": "Kerala"},
    "kochi": {"latitude": 9.9312, "longitude": 76.2673, "state": "Kerala"},
    "kollam": {"latitude": 8.8932, "longitude": 76.6141, "state": "Kerala"},
    "surat": {"latitude": 21.1702, "longitude": 72.8311, "state": "Gujarat"},
    "bhubaneswar": {"latitude": 20.2961, "longitude": 85.8245, "state": "Odisha"},
    "rajkot": {"latitude": 22.3039, "longitude": 70.8022, "state": "Gujarat"},
    "kota": {"latitude": 25.2138, "longitude": 75.8648, "state": "Rajasthan"},
    "bareilly": {"latitude": 28.3670, "longitude": 79.4304, "state": "Uttar Pradesh"},
    "mysore": {"latitude": 12.2958, "longitude": 76.6394, "state": "Karnataka"},
    "belgaum": {"latitude": 15.8497, "longitude": 74.4977, "state": "Karnataka"},
    "aurangabad": {"latitude": 19.8762, "longitude": 75.3433, "state": "Maharashtra"},
    "solapur": {"latitude": 17.6599, "longitude": 75.9064, "state": "Maharashtra"},
    "gurgaon": {"latitude": 28.4595, "longitude": 77.0266, "state": "Haryana"},
    "noida": {"latitude": 28.5355, "longitude": 77.3910, "state": "Uttar Pradesh"},
    "jalandhar": {"latitude": 31.3260, "longitude": 75.5762, "state": "Punjab"},
    "dehradun": {"latitude": 30.3165, "longitude": 78.0322, "state": "Uttarakhand"},
    "ranchi": {"latitude": 23.3441, "longitude": 85.3096, "state": "Jharkhand"},
    "cuttack": {"latitude": 20.4625, "longitude": 85.8830, "state": "Odisha"},
    "firozabad": {"latitude": 27.1477, "longitude": 78.4089, "state": "Uttar Pradesh"},
    "kochi": {"latitude": 9.9312, "longitude": 76.2673, "state": "Kerala"},
    "bhavnagar": {"latitude": 21.7645, "longitude": 72.1519, "state": "Gujarat"},
    "allahabad": {"latitude": 25.4358, "longitude": 81.8463, "state": "Uttar Pradesh"},
    "jamshedpur": {"latitude": 22.8046, "longitude": 86.2029, "state": "Jharkhand"},
    "asansol": {"latitude": 23.6850, "longitude": 86.9669, "state": "West Bengal"},
    "nanded": {"latitude": 19.1383, "longitude": 77.3210, "state": "Maharashtra"},
    "kolhapur": {"latitude": 16.7050, "longitude": 74.2433, "state": "Maharashtra"},
    "ajmer": {"latitude": 26.4499, "longitude": 74.6399, "state": "Rajasthan"},
    "akola": {"latitude": 20.7000, "longitude": 77.0083, "state": "Maharashtra"},
    "gulbarga": {"latitude": 17.3297, "longitude": 76.8343, "state": "Karnataka"},
    "jamnagar": {"latitude": 22.4707, "longitude": 70.0577, "state": "Gujarat"},
    "ujjain": {"latitude": 23.1763, "longitude": 75.7885, "state": "Madhya Pradesh"},
    "loni": {"latitude": 28.7543, "longitude": 77.5152, "state": "Uttar Pradesh"},
    "siliguri": {"latitude": 26.7271, "longitude": 88.3958, "state": "West Bengal"},
    "jhansi": {"latitude": 25.4484, "longitude": 78.5685, "state": "Uttar Pradesh"},
    "ulhasnagar": {"latitude": 19.2183, "longitude": 73.1653, "state": "Maharashtra"},
    "navi mumbai": {"latitude": 19.0330, "longitude": 73.0297, "state": "Maharashtra"},
    "jammu": {"latitude": 32.7266, "longitude": 74.8570, "state": "Jammu & Kashmir"},
    "sangli": {"latitude": 16.8524, "longitude": 74.5815, "state": "Maharashtra"},
    "mangalore": {"latitude": 12.9141, "longitude": 74.8560, "state": "Karnataka"},
    "erode": {"latitude": 11.3410, "longitude": 77.7182, "state": "Tamil Nadu"},
    "belgaum": {"latitude": 15.8497, "longitude": 74.4977, "state": "Karnataka"},
    "ambattur": {"latitude": 13.1173, "longitude": 80.1612, "state": "Tamil Nadu"},
    "tirunelveli": {"latitude": 8.7139, "longitude": 77.7567, "state": "Tamil Nadu"},
    "malegaon": {"latitude": 20.5581, "longitude": 74.5330, "state": "Maharashtra"},
    "gaya": {"latitude": 24.7928, "longitude": 85.0017, "state": "Bihar"},
    "jalgaon": {"latitude": 21.0093, "longitude": 75.5619, "state": "Maharashtra"},
    "udaipur": {"latitude": 24.5854, "longitude": 73.7125, "state": "Rajasthan"},
    "maheshtala": {"latitude": 22.2791, "longitude": 88.2731, "state": "West Bengal"}
}

# Indian states with their capital coordinates (for broader location detection)
INDIAN_STATES = {
    "andhra pradesh": {"latitude": 15.9129, "longitude": 79.7400, "capital": "amaravati"},
    "arunachal pradesh": {"latitude": 28.2180, "longitude": 94.7278, "capital": "itanagar"},
    "assam": {"latitude": 26.2006, "longitude": 92.9376, "capital": "dispur"},
    "bihar": {"latitude": 25.0961, "longitude": 85.3131, "capital": "patna"},
    "chhattisgarh": {"latitude": 21.2787, "longitude": 81.8661, "capital": "raipur"},
    "goa": {"latitude": 15.4909, "longitude": 73.8278, "capital": "panaji"},
    "gujarat": {"latitude": 22.2587, "longitude": 71.1924, "capital": "gandhinagar"},
    "haryana": {"latitude": 29.0588, "longitude": 76.0856, "capital": "chandigarh"},
    "himachal pradesh": {"latitude": 31.1048, "longitude": 77.1734, "capital": "shimla"},
    "jammu & kashmir": {"latitude": 33.7782, "longitude": 76.5762, "capital": "srinagar"},
    "jharkhand": {"latitude": 23.6102, "longitude": 85.2799, "capital": "ranchi"},
    "karnataka": {"latitude": 15.3173, "longitude": 75.7139, "capital": "bengaluru"},
    "kerala": {"latitude": 10.8505, "longitude": 76.2711, "capital": "thiruvananthapuram"},
    "madhya pradesh": {"latitude": 22.9734, "longitude": 78.6569, "capital": "bhopal"},
    "maharashtra": {"latitude": 19.0760, "longitude": 72.8777, "capital": "mumbai"},
    "manipur": {"latitude": 24.6637, "longitude": 93.9063, "capital": "imphal"},
    "meghalaya": {"latitude": 25.4670, "longitude": 91.3662, "capital": "shillong"},
    "mizoram": {"latitude": 23.1645, "longitude": 92.9376, "capital": "aizawl"},
    "nagaland": {"latitude": 26.1584, "longitude": 94.5624, "capital": "kohima"},
    "odisha": {"latitude": 20.9517, "longitude": 85.0985, "capital": "bhubaneswar"},
    "punjab": {"latitude": 31.1471, "longitude": 75.3412, "capital": "chandigarh"},
    "rajasthan": {"latitude": 27.0238, "longitude": 74.2179, "capital": "jaipur"},
    "sikkim": {"latitude": 27.5330, "longitude": 88.5122, "capital": "gangtok"},
    "tamil nadu": {"latitude": 11.1271, "longitude": 78.6569, "capital": "chennai"},
    "telangana": {"latitude": 17.1232, "longitude": 78.6569, "capital": "hyderabad"},
    "tripura": {"latitude": 23.8315, "longitude": 91.2868, "capital": "agartala"},
    "uttar pradesh": {"latitude": 26.8467, "longitude": 80.9462, "capital": "lucknow"},
    "uttarakhand": {"latitude": 30.0668, "longitude": 79.0193, "capital": "dehradun"},
    "west bengal": {"latitude": 22.9868, "longitude": 87.8550, "capital": "kolkata"},
    "delhi": {"latitude": 28.6139, "longitude": 77.2090, "capital": "delhi"},
    "pondicherry": {"latitude": 11.9416, "longitude": 79.8083, "capital": "pondicherry"},
    "chandigarh": {"latitude": 30.7333, "longitude": 76.7794, "capital": "chandigarh"},
    "dadra and nagar haveli": {"latitude": 20.1804, "longitude": 73.0169, "capital": "silvassa"},
    "daman and diu": {"latitude": 20.4283, "longitude": 72.8397, "capital": "daman"},
    "lakshadweep": {"latitude": 10.5726, "longitude": 72.6417, "capital": "kavaratti"},
    "andaman and nicobar islands": {"latitude": 11.6230, "longitude": 92.4623, "capital": "port blair"}
}

class LocationDetector:
    """Service to detect location from user queries"""
    
    @staticmethod
    def extract_location_from_query(query: str) -> Optional[Dict[str, any]]:
        """
        Extract location information from a user query
        Returns location dict with latitude, longitude, district, state if found
        """
        if not query:
            return None
        
        query_lower = query.lower()
        
        # Check for cities first (more specific)
        for city_name, city_data in INDIAN_CITIES.items():
            # Check for exact city name or partial match
            if city_name in query_lower:
                return {
                    "latitude": city_data["latitude"],
                    "longitude": city_data["longitude"],
                    "district": city_name.title(),
                    "state": city_data["state"],
                    "source": "city_detection",
                    "confidence": "high"
                }
        
        # Check for states (broader location)
        for state_name, state_data in INDIAN_STATES.items():
            if state_name in query_lower:
                return {
                    "latitude": state_data["latitude"],
                    "longitude": state_data["longitude"],
                    "district": state_data["capital"].title(),
                    "state": state_name.title(),
                    "source": "state_detection",
                    "confidence": "medium"
                }
        
        # Check for common location indicators
        location_patterns = [
            r'in\s+([a-zA-Z\s]+)',  # "in Ahmedabad", "in Gujarat"
            r'at\s+([a-zA-Z\s]+)',  # "at Mumbai", "at Pune"
            r'from\s+([a-zA-Z\s]+)',  # "from Bangalore"
            r'near\s+([a-zA-Z\s]+)',  # "near Delhi"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                location_name = match.strip()
                
                # Check if this matches any city
                if location_name in INDIAN_CITIES:
                    city_data = INDIAN_CITIES[location_name]
                    return {
                        "latitude": city_data["latitude"],
                        "longitude": city_data["longitude"],
                        "district": location_name.title(),
                        "state": city_data["state"],
                        "source": "pattern_detection",
                        "confidence": "high"
                    }
                
                # Check if this matches any state
                if location_name in INDIAN_STATES:
                    state_data = INDIAN_STATES[location_name]
                    return {
                        "latitude": state_data["latitude"],
                        "longitude": state_data["longitude"],
                        "district": state_data["capital"].title(),
                        "state": location_name.title(),
                        "source": "pattern_detection",
                        "confidence": "medium"
                    }
        
        return None
    
    @staticmethod
    def get_default_location() -> Dict[str, any]:
        """Return default location (Delhi) when no location is detected"""
        return {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "district": "Delhi",
            "state": "Delhi",
            "source": "default",
            "confidence": "low"
        }
    
    @staticmethod
    def detect_and_format_location(query: str) -> Tuple[Dict[str, any], bool]:
        """
        Detect location from query and return formatted location dict
        Returns: (location_dict, was_location_detected)
        """
        detected_location = LocationDetector.extract_location_from_query(query)
        
        if detected_location:
            return detected_location, True
        else:
            return LocationDetector.get_default_location(), False
