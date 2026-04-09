from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.schemas.component import ComponentResponse

router = APIRouter()

@router.get("/", response_model=List[ComponentResponse])
async def get_all_components(db: AsyncSession = Depends(get_db)):
    """
    Obtiene todo el catálogo de componentes activos de la base de datos.
    """
    try:
        query = text("SELECT * FROM components WHERE is_active = TRUE ORDER BY category, name")
        result = await db.execute(query)
        
        components = result.mappings().all()
        
        return components
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el catálogo: {str(e)}")