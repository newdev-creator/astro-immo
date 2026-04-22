import asyncio
from .database import SessionLocal, init_db
from .models import User, Role
from .auth import hash_password

async def seed():
    await init_db()
    async with SessionLocal() as db:
        patron = User(
            nom="Freisa",
            prenom="Julien",
            email="julien@immo.fr",
            hashed_password=hash_password("admin1234"),
            role=Role.patron
        )
        db.add(patron)
        await db.commit()
        print("Patron créé ✅")

asyncio.run(seed())