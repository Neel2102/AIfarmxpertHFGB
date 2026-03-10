"""
Authorized Farmer Coach Agent
STRICT RULES: Only authorized government domains, no summarization, direct extraction
"""

from typing import List, Dict, Any
from ..models.input_model import FarmerQueryInput, SchemeData
from ..models.output_model import FarmerQueryOutput, SchemeInfo
from ..services.authorized_web_search import AuthorizedWebSearchService


class AuthorizedFarmerCoachAgent:
    """
    Agent that ONLY retrieves REAL and AUTHORIZED Indian government agriculture schemes
    STRICT RULES: No summarization, no rewriting, direct extraction only
    """
    
    def __init__(self):
        self.web_service = AuthorizedWebSearchService()
    
    def process_query(self, input_data: FarmerQueryInput) -> FarmerQueryOutput:
        """
        Process farmer query following strict rules
        
        Args:
            input_data: Farmer query and language
            
        Returns:
            Direct extraction from authorized government sources
        """
        farmer_query = input_data.farmer_query
        language = input_data.language
        
        # Step 1: Perform real-time web search
        authorized_schemes = self.web_service.search_authorized_schemes(farmer_query)
        
        # Step 2: Convert to output format WITHOUT modification
        schemes = []
        for scheme_data in authorized_schemes:
            scheme_info = SchemeInfo(
                scheme_name=scheme_data['scheme_name'],  # EXACT as found
                simple_explanation=scheme_data['description'],  # NO summarization
                official_link=scheme_data['official_url']  # EXACT government URL
            )
            schemes.append(scheme_info)
        
        # Step 3: Return response
        if not schemes:
            # No authorized scheme found
            return FarmerQueryOutput(
                response_type="scheme_information",
                language=language,
                schemes=[],
                disclaimer="No official government scheme found for this query."
            )
        
        return FarmerQueryOutput(
            response_type="scheme_information",
            language=language,
            schemes=schemes,
            disclaimer="This information is extracted directly from official government websites. For applications and latest updates, please visit the official website."
        )
    
    def validate_authorized_domain(self, url: str) -> bool:
        """Validate URL is from authorized government domain"""
        return self.web_service.is_authorized_domain(url)
    
    def get_supported_languages(self) -> List[str]:
        """Return supported languages"""
        return ["English", "Hindi", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati"]
    
    def search_specific_scheme(self, scheme_name: str) -> Dict[str, Any]:
        """Search for specific scheme by name"""
        return self.web_service.get_scheme_by_exact_name(scheme_name)
