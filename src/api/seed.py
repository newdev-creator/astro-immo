import asyncio
import selectors

from .auth import hash_password
from .database import SessionLocal, init_db
from .models import Role, User


async def seed():
    await init_db()
    async with SessionLocal() as db:
        patron = User(
            nom="Freisa",
            prenom="Julien",
            email="julien@immo.fr",
            hashed_password=hash_password("admin1234"),
            role=Role.patron,
        )
        db.add(patron)
        await db.commit()
        print("Patron créé ✅")


asyncio.run(seed())

# Fix Windows ProactorEventLoop
asyncio.run(
    seed(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
)
