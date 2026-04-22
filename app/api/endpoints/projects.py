from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any

from app.db.database import get_db
from app.schemas.project import ProjectCreate, ProjectComponentAdd, ProjectValidationResponse

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo proyecto vacío en la base de datos.
    """
    try:
        query = text("""
            INSERT INTO projects (name, description)
            VALUES (:name, :description)
            RETURNING id
        """)
        
        result = await db.execute(query, {
            "name": project.name,
            "description": project.description
        })
        await db.commit()
        
        project_id = result.scalar()
        return {"project_id": project_id, "message": "Proyecto creado exitosamente"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el proyecto: {str(e)}")

@router.post("/{project_id}/components", status_code=status.HTTP_201_CREATED)
async def add_component_to_project(
    project_id: str, 
    component_data: ProjectComponentAdd, 
    db: AsyncSession = Depends(get_db)
):
    """
    Agrega piezas a un proyecto en la tabla pivote project_components.
    """
    check_component_query = text("SELECT id FROM components WHERE id = :component_id")
    component_result = await db.execute(check_component_query, {"component_id": component_data.component_id})
    if not component_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"El componente con ID {component_data.component_id} no existe."
        )

    try:
        query = text("""
            INSERT INTO project_components (project_id, component_id, quantity)
            VALUES (:project_id, :component_id, :quantity)
        """)
        
        await db.execute(query, {
            "project_id": project_id,
            "component_id": component_data.component_id,
            "quantity": component_data.quantity
        })
        await db.commit()
        
        return {"message": "Componente agregado al proyecto correctamente"}
        
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Error de integridad: Verifica que el proyecto exista y que el componente no haya sido agregado previamente."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al agregar el componente: {str(e)}")

@router.get("/{project_id}/validation", response_model=ProjectValidationResponse)
async def get_project_validation(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    Consulta la vista de validación para un proyecto y devuelve el estado de compatibilidad.
    """
    query = text("SELECT * FROM vw_project_validation WHERE project_id = :pid")
    result = await db.execute(query, {"pid": project_id})
    row = result.mappings().first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No se encontró validación para el proyecto {project_id}. Verifica que exista y tenga componentes."
        )
        
    return row
