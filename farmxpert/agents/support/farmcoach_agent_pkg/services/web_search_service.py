"""
Web Search Service for fetching government scheme data from official sources
"""

import requests
import json
from typing import List, Dict, Any
from ..models.input_model import SchemeData


class WebSearchService:
    """Service to fetch government scheme data from official web sources"""
    
    def __init__(self):
        self.data_gov_in_base_url = "https://api.data.gov.in"
        self.gov_schemes_api = "https://api.data.gov.in/catalog/api"
        
    def fetch_schemes_from_data_gov_in(self, query: str = "agriculture schemes") -> List[Dict[str, Any]]:
        """
        Fetch scheme data from data.gov.in API
        
        Args:
            query: Search query for schemes
            
        Returns:
            List of scheme dictionaries
        """
        try:
            # This is a mock implementation - in production you'd use real API endpoints
            # data.gov.in requires API key and specific endpoints
            
            # Mock API response structure
            mock_response = {
                "status": "success",
                "records": [
                    {
                        "scheme_name": "Pradhan Mantri Fasal Bima Yojana",
                        "ministry": "Ministry of Agriculture & Farmers Welfare",
                        "description": "Crop insurance scheme providing financial support to farmers in case of crop loss due to natural calamities, pests, or diseases. Premium rates are only 2% for Kharif crops, 1.5% for Rabi crops, and 5% for commercial/horticultural crops.",
                        "state": "All",
                        "official_url": "https://pmfby.gov.in"
                    },
                    {
                        "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                        "ministry": "Ministry of Agriculture & Farmers Welfare", 
                        "description": "Income support scheme providing Rs. 6000 per year to small and marginal farmers in three equal installments of Rs. 2000 each. Direct benefit transfer to farmer's bank account.",
                        "state": "All",
                        "official_url": "https://pmkisan.gov.in"
                    },
                    {
                        "scheme_name": "Kisan Credit Card (KCC)",
                        "ministry": "Ministry of Agriculture & Farmers Welfare",
                        "description": "Credit facility for farmers to meet agricultural requirements including cultivation costs and post-harvest expenses. Provides timely credit support with flexible repayment options and interest subvention.",
                        "state": "All",
                        "official_url": "https://kisan.gov.in"
                    },
                    {
                        "scheme_name": "Soil Health Card Scheme",
                        "ministry": "Ministry of Agriculture & Farmers Welfare",
                        "description": "Scheme to provide soil health cards to farmers containing information on soil nutrient status and recommendations for fertilizer application. Helps in maintaining soil health and reducing fertilizer costs.",
                        "state": "All",
                        "official_url": "https://soilhealth.dac.gov.in"
                    },
                    {
                        "scheme_name": "Paramparagat Krishi Vikas Yojana (PKVY)",
                        "ministry": "Ministry of Agriculture & Farmers Welfare",
                        "description": "Promotes organic farming and provides financial assistance of Rs. 50,000 per hectare for 3 years for cluster-based organic farming. Supports conversion to organic agriculture.",
                        "state": "All",
                        "official_url": "https://pgsindia-ncof.gov.in"
                    }
                ]
            }
            
            return mock_response.get("records", [])
            
        except Exception as e:
            print(f"Error fetching from data.gov.in: {e}")
            return []
    
    def fetch_schemes_from_official_websites(self) -> List[Dict[str, Any]]:
        """
        Fetch scheme data by scraping official government websites
        
        Returns:
            List of scheme dictionaries
        """
        # This would implement web scraping in production
        # For demo, returning mock data
        return self.fetch_schemes_from_data_gov_in()
    
    def search_schemes(self, query: str = "agriculture schemes") -> List[SchemeData]:
        """
        Search for schemes using web search
        
        Args:
            query: Search query
            
        Returns:
            List of SchemeData objects
        """
        print(f"🔍 Searching web for: '{query}'")
        
        # Try multiple sources
        schemes_data = []
        
        # 1. Try data.gov.in API
        api_schemes = self.fetch_schemes_from_data_gov_in(query)
        schemes_data.extend(api_schemes)
        
        # 2. Try official websites (web scraping)
        web_schemes = self.fetch_schemes_from_official_websites()
        schemes_data.extend(web_schemes)
        
        # Convert to SchemeData objects
        scheme_objects = []
        seen_schemes = set()  # Avoid duplicates
        
        for scheme_dict in schemes_data:
            scheme_name = scheme_dict.get("scheme_name", "")
            if scheme_name and scheme_name not in seen_schemes:
                scheme = SchemeData(
                    scheme_name=scheme_name,
                    ministry=scheme_dict.get("ministry", ""),
                    description=scheme_dict.get("description", ""),
                    state=scheme_dict.get("state", "All"),
                    official_url=scheme_dict.get("official_url", "")
                )
                scheme_objects.append(scheme)
                seen_schemes.add(scheme_name)
        
        print(f"✅ Found {len(scheme_objects)} unique schemes")
        return scheme_objects
    
    def get_scheme_by_name(self, scheme_name: str) -> SchemeData:
        """
        Get specific scheme by name
        
        Args:
            scheme_name: Name of the scheme to search for
            
        Returns:
            SchemeData object or None if not found
        """
        schemes = self.search_schemes(scheme_name)
        
        for scheme in schemes:
            if scheme_name.lower() in scheme.scheme_name.lower():
                return scheme
        
        return None
