from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GrowthLocation(BaseModel):
    latitude: float
    longitude: float
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"


class CropInfo(BaseModel):
    crop_name: str                      # e.g. Wheat, Cotton
    sowing_date: Optional[datetime]     # if known
    variety: Optional[str] = None


class CropImage(BaseModel):
    image_id: str                       # UUID or filename
    image_url: str                      # storage path / S3 URL
    captured_at: datetime
    angle: Optional[str] = Field(
        default=None,
        description="top, side, mixed"
    )


class GrowthMonitorInput(BaseModel):
    farmer_id: str
    field_id: str
    crop: CropInfo
    location: GrowthLocation
    images: List[CropImage]
    triggered_at: datetime
