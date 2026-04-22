from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra un nuevo usuario en la base de datos validando que el email no exista.
    """
    query_check = text("SELECT id FROM users WHERE email = :email")
    result = await db.execute(query_check, {"email": user_in.email})
    if result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )

    hashed_password = get_password_hash(user_in.password)
    
    query_insert = text("""
        INSERT INTO users (email, password_hash)
        VALUES (:email, :password_hash)
        RETURNING id, email, created_at
    """)
    try:
        new_user = await db.execute(query_insert, {
            "email": user_in.email,
            "password_hash": hashed_password
        })
        user_row = new_user.mappings().first()
        await db.commit()
        return user_row
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")

@router.post("/login", response_model=Token)
async def login(credentials: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Inicia sesión y devuelve un token JWT. Usa 'username' como el equivalente a 'email'.
    """
    query_user = text("SELECT id, email, password_hash FROM users WHERE email = :email")
    result = await db.execute(query_user, {"email": credentials.username})
    user_row = result.mappings().first()

    if not user_row or not verify_password(credentials.password, user_row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(user_row["id"])},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
