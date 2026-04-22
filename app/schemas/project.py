from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectComponentAdd(BaseModel):
    component_id: str 
    quantity: int = 1

class ProjectValidationResponse(BaseModel):
    project_id: str
    project_name: str
    brain_name: Optional[str] = None
    total_available_ma: int
    total_consumed_ma: int
    remaining_ma: int
    is_overloaded: bool
    is_critical_margin: bool
    voltage_status: str

    model_config = ConfigDict(from_attributes=True)
