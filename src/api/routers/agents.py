from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import hash_password, require_patron
from ..database import get_db
from ..models import Role, User

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    nom: str
    prenom: str
    email: str
    password: str


class AgentUpdate(BaseModel):
    nom: str
    prenom: str
    email: str
    password: Optional[str] = None


@router.get("/")
async def list_agents(
    db: AsyncSession = Depends(get_db), _: User = Depends(require_patron)
):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.post("/", status_code=201)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_patron),
):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    agent = User(
        nom=data.nom,
        prenom=data.prenom,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=Role.agent,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.put("/{agent_id}")
async def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_patron),
):
    result = await db.execute(select(User).where(User.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    agent.nom = data.nom
    agent.prenom = data.prenom
    agent.email = data.email
    if data.password:
        agent.hashed_password = hash_password(data.password)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    patron: User = Depends(require_patron),
):
    if agent_id == patron.id:
        raise HTTPException(
            status_code=400, detail="Impossible de se supprimer soi-même"
        )
    result = await db.execute(select(User).where(User.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    await db.delete(agent)
    await db.commit()
