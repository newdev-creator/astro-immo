import asyncio
import sys

from sqlalchemy import select

from .auth import hash_password
from .database import SessionLocal, init_db
from .models import Role, User


async def seed():
    await init_db()
    async with SessionLocal() as db:
        existing_user = await db.scalar(
            select(User).where(User.email == "julien@immo.fr")
        )
        if existing_user:
            print("Utilisateur deja present, seed ignore")
            return

        patron = User(
            nom="Freisa",
            prenom="Julien",
            email="julien@immo.fr",
            hashed_password=hash_password("admin1234"),
            role=Role.patron,
        )
        db.add(patron)
        await db.commit()
        print("Patron cree avec succes")


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
