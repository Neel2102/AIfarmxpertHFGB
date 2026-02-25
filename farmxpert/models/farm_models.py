from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from farmxpert.models.database import Base

class Farm(Base):
    __tablename__ = "farms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    size_acres = Column(Float, nullable=False)
    farmer_name = Column(String(255), nullable=False)
    farmer_phone = Column(String(20))
    farmer_email = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    fields = relationship("Field", back_populates="farm")
    soil_tests = relationship("SoilTest", back_populates="farm")
    crops = relationship("Crop", back_populates="farm")
    tasks = relationship("Task", back_populates="farm")
    weather_data = relationship("WeatherData", back_populates="farm")

class Field(Base):
    __tablename__ = "fields"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    name = Column(String(255), nullable=False)
    size_acres = Column(Float, nullable=False)
    soil_type = Column(String(100))
    irrigation_type = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    farm = relationship("Farm", back_populates="fields")
    crops = relationship("Crop", back_populates="field")
    soil_tests = relationship("SoilTest", back_populates="field")

class SoilTest(Base):
    __tablename__ = "soil_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("fields.id"))
    test_date = Column(DateTime(timezone=True), nullable=False)
    ph_level = Column(Float)
    nitrogen_ppm = Column(Float)
    phosphorus_ppm = Column(Float)
    potassium_ppm = Column(Float)
    organic_matter_percent = Column(Float)
    soil_texture = Column(String(50))
    test_lab = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    farm = relationship("Farm", back_populates="soil_tests")
    field = relationship("Field", back_populates="soil_tests")

class Crop(Base):
    __tablename__ = "crops"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("fields.id"))
    crop_type = Column(String(100), nullable=False)
    variety = Column(String(100))
    planting_date = Column(DateTime(timezone=True))
    expected_harvest_date = Column(DateTime(timezone=True))
    area_acres = Column(Float, nullable=False)
    seed_quantity = Column(Float)
    seed_cost = Column(Float)
    status = Column(String(50), default="planted")  # planted, growing, harvested
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    farm = relationship("Farm", back_populates="crops")
    field = relationship("Field", back_populates="crops")
    tasks = relationship("Task", back_populates="crop")
    yields = relationship("Yield", back_populates="crop")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crops.id"))
    task_type = Column(String(100), nullable=False)  # planting, fertilizing, irrigation, harvesting, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    completed_date = Column(DateTime(timezone=True))
    priority = Column(String(20), default="medium")  # low, medium, high
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled
    assigned_to = Column(String(255))
    cost = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    farm = relationship("Farm", back_populates="tasks")
    crop = relationship("Crop", back_populates="tasks")

class Yield(Base):
    __tablename__ = "yields"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    harvest_date = Column(DateTime(timezone=True), nullable=False)
    quantity_tons = Column(Float, nullable=False)
    quality_grade = Column(String(20))  # A, B, C, etc.
    moisture_percent = Column(Float)
    price_per_ton = Column(Float)
    total_value = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    crop = relationship("Crop", back_populates="yields")

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    temperature_high = Column(Float)
    temperature_low = Column(Float)
    humidity = Column(Float)
    precipitation_mm = Column(Float)
    wind_speed_kmh = Column(Float)
    wind_direction = Column(String(10))
    pressure_hpa = Column(Float)
    uv_index = Column(Float)
    forecast_data = Column(JSON)  # Store extended forecast data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    farm = relationship("Farm", back_populates="weather_data")

class MarketPrice(Base):
    __tablename__ = "market_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_type = Column(String(100), nullable=False)
    market_location = Column(String(255), nullable=False)
    price_per_ton = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(255))
    quality_grade = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentInteraction(Base):
    __tablename__ = "agent_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_data = Column(JSON)
    response_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    farm = relationship("Farm")

class FarmEquipment(Base):
    __tablename__ = "farm_equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    equipment_type = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    model = Column(String(100))
    year = Column(Integer)
    capacity = Column(String(100))
    fuel_type = Column(String(50))
    maintenance_schedule = Column(JSON)
    last_maintenance = Column(DateTime(timezone=True))
    next_maintenance = Column(DateTime(timezone=True))
    status = Column(String(20), default="active")  # active, maintenance, retired
    purchase_cost = Column(Float)
    current_value = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    farm = relationship("Farm")
