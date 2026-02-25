from pydantic import BaseModel
from typing import List


class SchemeData(BaseModel):
    scheme_name: str
    ministry: str
    description: str
    state: str
    official_url: str


class FarmerQueryInput(BaseModel):
    farmer_query: str
    language: str
    schemes_data: List[SchemeData]
