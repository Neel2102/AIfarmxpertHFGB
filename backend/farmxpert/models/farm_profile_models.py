"""
Farm Profile Models for Onboarding Data
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from farmxpert.models.database import Base

class FarmProfile(Base):
    """Farm profile model for storing onboarding data"""
    __tablename__ = "farm_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Basic Farm Information
    farm_name = Column(String(255), nullable=True)
    farm_size = Column(String(100), nullable=True)
    farm_size_unit = Column(String(20), nullable=True)  # acres, hectares, etc.
    location = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    village = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Soil Information
    soil_type = Column(String(100), nullable=True)
    soil_ph = Column(String(20), nullable=True)
    soil_organic_matter = Column(String(50), nullable=True)
    soil_texture = Column(String(100), nullable=True)
    soil_drainage = Column(String(100), nullable=True)
    
    # Water Source
    water_source = Column(String(100), nullable=True)
    irrigation_method = Column(String(100), nullable=True)
    water_availability = Column(String(100), nullable=True)
    
    # Crop Information
    primary_crops = Column(JSON, nullable=True)  # List of crops
    crop_rotation = Column(String(100), nullable=True)
    cropping_season = Column(String(100), nullable=True)
    specific_crop = Column(String(255), nullable=True)
    
    # Farming Practices
    farming_experience = Column(String(100), nullable=True)
    labor_setup = Column(String(100), nullable=True)
    machinery = Column(JSON, nullable=True)  # List of machinery
    
    # Sustainability Practices
    sustainability_focus = Column(JSON, nullable=True)  # List of practices
    pest_management = Column(String(100), nullable=True)
    fertilizer_approach = Column(String(100), nullable=True)
    
    # Technology & Goals
    tech_comfort = Column(String(100), nullable=True)
    farm_goals = Column(JSON, nullable=True)  # List of goals
    challenges = Column(String(500), nullable=True)
    
    # Additional Information
    additional_info = Column(Text, nullable=True)

    # Farm polygon (GeoJSON) from the Farm Layout map tool
    farm_polygon = Column(JSON, nullable=True)
    # Farm layout form data (soil_type, water_source, season, etc.)
    farm_layout_data = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FarmProfile(user_id={self.user_id}, farm_name={self.farm_name})>"
