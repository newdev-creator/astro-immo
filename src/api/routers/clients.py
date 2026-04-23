from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import User, get_current_user
from ..database import get_db
from ..models import Client

router = APIRouter(prefix="/api/clients", tags=["clients"])


class ClientCreate(BaseModel):
    nom: str
    prenom: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    budget: Optional[float] = None


class ClientUpdate(ClientCreate):
    pass


@router.get("/")
async def list_clients(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    if user.role == "patron":
        result = await db.execute(select(Client))
    else:
        result = await db.execute(select(Client).where(Client.agent_id == user.id))
    return result.scalars().all()


@router.get("/{client_id}")
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if user.role != "patron" and client.agent_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return client


@router.post("/", status_code=201)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    client = Client(**data.model_dump(), agent_id=user.id)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.put("/{client_id}")
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if user.role != "patron" and client.agent_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    for key, value in data.model_dump().items():
        setattr(client, key, value)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if user.role != "patron" and client.agent_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    await db.delete(client)
    await db.commit()
