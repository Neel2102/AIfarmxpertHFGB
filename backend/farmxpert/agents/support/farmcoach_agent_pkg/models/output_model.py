from pydantic import BaseModel
from typing import List


class SchemeInfo(BaseModel):
    scheme_name: str
    simple_explanation: str
    official_link: str


class FarmerQueryOutput(BaseModel):
    response_type: str = "scheme_information"
    language: str
    schemes: List[SchemeInfo]
    disclaimer: str
