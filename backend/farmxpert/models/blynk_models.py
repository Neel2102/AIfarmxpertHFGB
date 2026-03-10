"""
Blynk Device and Sensor Reading Models
"""

from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, Boolean, Numeric,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from farmxpert.models.database import Base


class BlynkDevice(Base):
    """Blynk IoT device registered by a farmer"""
    __tablename__ = "blynk_devices"

    id = Column(BigInteger, primary_key=True, index=True)
    farm_id = Column(BigInteger, nullable=False, index=True)  # resolved server-side, always set
    device_name = Column(String(255), default="My Blynk Device")
    blynk_device_id = Column(String(100), unique=True, nullable=True)
    auth_token = Column(Text, nullable=False)           # stored encrypted
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="active")       # active | offline | invalid_token
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: no FK/relationship — farm_id is a logical reference only.
    # No relationship to SensorReading because partitioned tables
    # cannot have FK constraints in PostgreSQL < 17.


class SensorReading(Base):
    """Individual sensor reading from a Blynk device (high-volume, partitioned)"""
    __tablename__ = "sensor_readings"
    __table_args__ = (
        {"implicit_returning": False},  # Required for partitioned tables
    )

    id = Column(BigInteger, primary_key=True)
    device_id = Column(BigInteger, nullable=False, index=True)
    farm_id = Column(BigInteger, nullable=False, index=True)

    # 9 Blynk sensor parameters
    air_temperature = Column(Numeric(7, 2))
    air_humidity = Column(Numeric(7, 2))
    soil_moisture = Column(Numeric(7, 2))
    soil_temperature = Column(Numeric(7, 2))
    soil_ec = Column(Numeric(7, 2))
    soil_ph = Column(Numeric(5, 2))
    nitrogen = Column(Numeric(7, 2))
    phosphorus = Column(Numeric(7, 2))
    potassium = Column(Numeric(7, 2))

    # Metadata
    raw_payload = Column(JSONB, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: no FK/relationship to BlynkDevice — partitioned tables
    # do not support foreign key constraints in PostgreSQL < 17.


class SensorDailySummary(Base):
    """Pre-aggregated daily sensor averages per farm"""
    __tablename__ = "sensor_daily_summary"
    __table_args__ = (
        UniqueConstraint("farm_id", "device_id", "summary_date", name="uq_sensor_daily_summary"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    farm_id = Column(BigInteger, ForeignKey("farms.id"), nullable=False)
    device_id = Column(BigInteger, nullable=True)
    summary_date = Column(DateTime, nullable=False)

    # Averages
    avg_air_temperature = Column(Numeric(7, 2))
    avg_air_humidity = Column(Numeric(7, 2))
    avg_soil_moisture = Column(Numeric(7, 2))
    avg_soil_temperature = Column(Numeric(7, 2))
    avg_soil_ec = Column(Numeric(7, 2))
    avg_soil_ph = Column(Numeric(5, 2))
    avg_nitrogen = Column(Numeric(7, 2))
    avg_phosphorus = Column(Numeric(7, 2))
    avg_potassium = Column(Numeric(7, 2))

    # Min / Max
    min_air_temperature = Column(Numeric(7, 2))
    max_air_temperature = Column(Numeric(7, 2))
    min_soil_moisture = Column(Numeric(7, 2))
    max_soil_moisture = Column(Numeric(7, 2))

    reading_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    farm = relationship("Farm")
