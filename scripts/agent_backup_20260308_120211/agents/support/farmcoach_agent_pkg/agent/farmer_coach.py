"""
Farmer Coach Agent - Core Agent Logic
Main agent that processes farmer queries and provides scheme information
"""

from typing import List
from ..models.input_model import FarmerQueryInput, SchemeData
from ..models.output_model import FarmerQueryOutput, SchemeInfo
from ..services.scheme_formatter import SchemeFormatter
from .rules import STANDARD_DISCLAIMER, validate_response_content


class FarmerCoachAgent:
    """Main agent class for providing government scheme information to farmers"""
    
    def __init__(self):
        self.formatter = SchemeFormatter()
    
    def process_query(self, input_data: FarmerQueryInput) -> FarmerQueryOutput:
        """
        Process farmer query and return scheme information
        
        Args:
            input_data: Farmer query and scheme data
            
        Returns:
            Formatted response with scheme information
        """
        # Step 1: Read farmer_query and schemes_data (already in input_data)
        farmer_query = input_data.farmer_query
        schemes_data = input_data.schemes_data
        language = input_data.language
        
        # Step 2: Match schemes relevant to the query (keyword-based only)
        matched_schemes = self.formatter.match_schemes_to_query(farmer_query, schemes_data)
        
        # Step 3: For each matched scheme, format the output
        formatted_schemes = []
        for scheme in matched_schemes:
            scheme_info = self.formatter.format_scheme_info(scheme)
            
            # Validate response content follows rules
            if validate_response_content(
                scheme_info.scheme_name, 
                scheme_info.simple_explanation, 
                scheme.description
            ):
                formatted_schemes.append(scheme_info)
        
        # Step 4: Handle case where no schemes match
        if not formatted_schemes:
            # If no specific matches, return all schemes with a general message
            for scheme in schemes_data[:3]:  # Limit to first 3 to avoid overwhelming
                scheme_info = self.formatter.format_scheme_info(scheme)
                formatted_schemes.append(scheme_info)
        
        # Step 5: Create response in output model format
        response = FarmerQueryOutput(
            response_type="scheme_information",
            language=language,
            schemes=formatted_schemes,
            disclaimer=STANDARD_DISCLAIMER
        )
        
        return response
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ["English", "Hindi", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati"]
    
    def validate_input(self, input_data: FarmerQueryInput) -> bool:
        """Validate input data meets requirements"""
        if not input_data.farmer_query.strip():
            return False
        
        if not input_data.language.strip():
            return False
        
        if not input_data.schemes_data:
            return False
        
        # Validate each scheme has required fields
        for scheme in input_data.schemes_data:
            if not all([scheme.scheme_name.strip(), scheme.description.strip(), scheme.official_url.strip()]):
                return False
        
        return True
