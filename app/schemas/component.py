from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal

class ComponentResponse(BaseModel):
    id: str
    name: str
    category: str
    logic_level: str
    voltage_min: Decimal
    voltage_max: Decimal
    current_draw_ma: int
    max_supply_ma: int
    image_url: Optional[str] = None 

    model_config = ConfigDict(from_attributes=True)