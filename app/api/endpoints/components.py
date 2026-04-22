from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import traceback
import logging

logger = logging.getLogger(__name__)

from app.db.database import get_db
from app.schemas.component import ComponentResponse
from app.services.currency import get_mxn_rate

router = APIRouter()

@router.get("/", response_model=List[ComponentResponse])
async def get_all_components(db: AsyncSession = Depends(get_db)):
    try:
        query = text("SELECT * FROM components WHERE is_active = TRUE ORDER BY category, name")
        result = await db.execute(query)
        componentes_db = result.mappings().all()

        tasa_cambio = await get_mxn_rate()

        lista_componentes = []
        
        for fila in componentes_db:
            componente_dict = dict(fila)
            componente_dict["id"] = str(componente_dict["id"])
            if componente_dict.get("price_usd") is not None:
                componente_dict["price_mxn"] = round(float(componente_dict["price_usd"]) * tasa_cambio, 2)
            lista_componentes.append(componente_dict)
            
        return lista_componentes
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"[{type(e).__name__}] {str(e)}")