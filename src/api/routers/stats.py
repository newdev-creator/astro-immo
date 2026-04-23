from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import User, get_current_user
from ..database import get_db
from ..models import Bien, Client, StatutBien

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/")
async def get_stats(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    if user.role == "patron":
        biens_filter = True
        clients_filter = True
    else:
        biens_filter = Bien.agent_id == user.id
        clients_filter = Client.agent_id == user.id

    biens_total = await db.execute(select(func.count(Bien.id)).where(biens_filter))
    biens_disponibles = await db.execute(
        select(func.count(Bien.id)).where(
            biens_filter if user.role == "patron" else Bien.agent_id == user.id,
            Bien.statut == StatutBien.disponible,
        )
    )
    biens_vendus = await db.execute(
        select(func.count(Bien.id)).where(
            biens_filter if user.role == "patron" else Bien.agent_id == user.id,
            Bien.statut == StatutBien.vendu,
        )
    )
    clients_total = await db.execute(
        select(func.count(Client.id)).where(clients_filter)
    )

    return {
        "biens_total": biens_total.scalar(),
        "biens_disponibles": biens_disponibles.scalar(),
        "biens_vendus": biens_vendus.scalar(),
        "clients_total": clients_total.scalar(),
    }
