import os
import re
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base

load_dotenv()

raw_url = os.getenv("DATABASE_URL")

if raw_url and raw_url.startswith("postgresql"):
    # Neon : postgresql -> postgresql+psycopg
    DATABASE_URL = re.sub(r"^postgresql:", "postgresql+psycopg:", raw_url)
    connect_args = {}
else:
    # Dev local : SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./immo.db"
    connect_args = {}

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
