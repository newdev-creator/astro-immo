from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from ..database import get_db
from ..models import User
from ..auth import verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginData, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = create_token({"sub": str(user.id), "role": user.role, "nom": user.nom})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600 * 8
    )
    return {"message": "Connecté", "role": user.role}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Déconnecté"}