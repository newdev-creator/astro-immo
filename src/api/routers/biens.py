from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import User, get_current_user
from ..cloudinary import delete_image, upload_image
from ..database import get_db
from ..models import Bien, StatutBien, TypeBien

router = APIRouter(prefix="/api/biens", tags=["biens"])


class BienCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    prix: float
    surface: Optional[float] = None
    ville: Optional[str] = None
    adresse: Optional[str] = None
    type_bien: TypeBien = TypeBien.appartement
    statut: StatutBien = StatutBien.disponible
    proprietaire_id: Optional[int] = None


class BienUpdate(BienCreate):
    pass


@router.get("/publics")
async def list_biens_publics(
    db: AsyncSession = Depends(get_db),
    type_bien: Optional[TypeBien] = None,
    ville: Optional[str] = None,
    prix_max: Optional[float] = None,
):
    query = select(Bien).where(Bien.statut == StatutBien.disponible)
    if type_bien:
        query = query.where(Bien.type_bien == type_bien)
    if ville:
        query = query.where(Bien.ville.ilike(f"%{ville}%"))
    if prix_max:
        query = query.where(Bien.prix <= prix_max)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/publics/{bien_id}")
async def get_bien_public(bien_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bien).where(Bien.id == bien_id, Bien.statut == StatutBien.disponible)
    )
    bien = result.scalar_one_or_none()
    if not bien:
        raise HTTPException(status_code=404, detail="Bien introuvable")
    return bien


@router.get("/")
async def list_biens(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    if user.role == "patron":
        result = await db.execute(select(Bien))
    else:
        result = await db.execute(select(Bien).where(Bien.agent_id == user.id))
    return result.scalars().all()


@router.get("/{bien_id}")
async def get_bien(
    bien_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bien).where(Bien.id == bien_id))
    bien = result.scalar_one_or_none()
    if not bien:
        raise HTTPException(status_code=404, detail="Bien introuvable")
    if user.role != "patron" and bien.agent_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return bien


@router.post("/", status_code=201)
async def create_bien(
    data: BienCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bien = Bien(**data.model_dump(), agent_id=user.id)
    db.add(bien)
    await db.commit()
    await db.refresh(bien)
    return bien


@router.post("/{bien_id}/image", status_code=201)
async def upload_bien_image(
    bien_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bien).where(Bien.id == bien_id))
    bien = result.scalar_one_or_none()
    if not bien:
        raise HTTPException(status_code=404, detail="Bien introuvable")
    if user.role != "patron" and bien.agent_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    if bien.image_url:
        await delete_image(bien.image_url)

    contents = await file.read()
    url = await upload_image(contents)
    bien.image_url = url
    await db.commit()
    await db.refresh(bien)
    return {"image_url": url}


@router.put("/{bien_id}")
async def update_bien(
    bien_id: int,
    data: BienUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bien).where(Bien.id == bien_id))
    bien = result.scalar_one_or_none()
    if not bien:
        raise HTTPException(status_code=404, detail="Bien introuvable")
    if user.role != "patron" and bien.agent_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    for key, value in data.model_dump().items():
        setattr(bien, key, value)
    await db.commit()
    await db.refresh(bien)
    return bien


@router.delete("/{bien_id}", status_code=204)
async def delete_bien(
    bien_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bien).where(Bien.id == bien_id))
    bien = result.scalar_one_or_none()
    if not bien:
        raise HTTPException(status_code=404, detail="Bien introuvable")
    if user.role != "patron" and bien.agent_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    await db.delete(bien)
    await db.commit()
