"""
Tests for Farmer Coach Agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agent.farmer_coach import FarmerCoachAgent
from models.input_model import FarmerQueryInput, SchemeData
from models.output_model import FarmerQueryOutput


class TestFarmerCoachAgent:
    """Test cases for FarmerCoachAgent"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.agent = FarmerCoachAgent()
        self.sample_scheme = SchemeData(
            scheme_name="Pradhan Mantri Fasal Bima Yojana",
            ministry="Ministry of Agriculture",
            description="Crop insurance scheme providing financial support to farmers in case of crop loss",
            state="All",
            official_url="https://pmfby.gov.in"
        )
    
    def test_agent_run_with_valid_input(self):
        """Test agent run method with valid input data"""
        # Create valid FarmerCoachInput with one sample scheme
        input_data = FarmerQueryInput(
            farmer_query="Crop insurance schemes",
            language="English",
            schemes_data=[self.sample_scheme]
        )
        
        # Call the agent's run method
        result = self.agent.process_query(input_data)
        
        # Assert response structure and content
        assert isinstance(result, FarmerQueryOutput)
        assert result.response_type == "scheme_information"
        assert result.language == "English"
        assert len(result.schemes) >= 1
        assert result.disclaimer is not None and len(result.disclaimer) > 0
        
        # Assert scheme details
        scheme = result.schemes[0]
        assert scheme.scheme_name == "Pradhan Mantri Fasal Bima Yojana"
        assert scheme.scheme_name.strip() != ""
        assert scheme.official_link.startswith("http")
        assert scheme.official_link == "https://pmfby.gov.in"
        assert scheme.simple_explanation is not None and len(scheme.simple_explanation) > 0
    
    def test_agent_with_multiple_schemes(self):
        """Test agent with multiple schemes"""
        schemes = [
            self.sample_scheme,
            SchemeData(
                scheme_name="Kisan Credit Card",
                ministry="Ministry of Finance",
                description="Credit facility for farmers to meet agricultural requirements",
                state="All",
                official_url="https://kisan.gov.in"
            )
        ]
        
        input_data = FarmerQueryInput(
            farmer_query="financial help for farmers",
            language="English",
            schemes_data=schemes
        )
        
        result = self.agent.process_query(input_data)
        
        assert len(result.schemes) >= 1
        assert result.response_type == "scheme_information"
        
        # Check all returned schemes have valid data
        for scheme in result.schemes:
            assert scheme.scheme_name.strip() != ""
            assert scheme.official_link.startswith("http")
            assert scheme.simple_explanation.strip() != ""
    
    def test_agent_with_no_matching_schemes(self):
        """Test agent when no schemes match the query"""
        unrelated_scheme = SchemeData(
            scheme_name="Unrelated Scheme",
            ministry="Ministry of Health",
            description="Health scheme for citizens",
            state="All",
            official_url="https://health.gov.in"
        )
        
        input_data = FarmerQueryInput(
            farmer_query="crop insurance",
            language="English",
            schemes_data=[unrelated_scheme]
        )
        
        result = self.agent.process_query(input_data)
        
        # Should still return schemes (fallback behavior)
        assert len(result.schemes) >= 1
        assert result.response_type == "scheme_information"
    
    def test_agent_input_validation(self):
        """Test agent input validation"""
        # Test empty farmer query
        invalid_input = FarmerQueryInput(
            farmer_query="",
            language="English",
            schemes_data=[self.sample_scheme]
        )
        
        assert not self.agent.validate_input(invalid_input)
        
        # Test empty language
        invalid_input2 = FarmerQueryInput(
            farmer_query="insurance",
            language="",
            schemes_data=[self.sample_scheme]
        )
        
        assert not self.agent.validate_input(invalid_input2)
        
        # Test empty schemes data
        invalid_input3 = FarmerQueryInput(
            farmer_query="insurance",
            language="English",
            schemes_data=[]
        )
        
        assert not self.agent.validate_input(invalid_input3)
        
        # Test valid input
        valid_input = FarmerQueryInput(
            farmer_query="insurance",
            language="English",
            schemes_data=[self.sample_scheme]
        )
        
        assert self.agent.validate_input(valid_input)
    
    def test_agent_supported_languages(self):
        """Test agent returns supported languages"""
        languages = self.agent.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "English" in languages
        assert "Hindi" in languages
    
    def test_agent_with_hindi_language(self):
        """Test agent with Hindi language input"""
        input_data = FarmerQueryInput(
            farmer_query="फसल बीमा योजना",
            language="Hindi",
            schemes_data=[self.sample_scheme]
        )
        
        result = self.agent.process_query(input_data)
        
        assert result.language == "Hindi"
        assert result.response_type == "scheme_information"
        assert len(result.schemes) >= 1
