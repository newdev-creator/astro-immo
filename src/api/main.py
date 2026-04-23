from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from .database import init_db
from .routers.agents import router as agents_router
from .routers.auth import router as auth_router
from .routers.biens import router as biens_router
from .routers.clients import router as clients_router
from .routers.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(biens_router)
app.include_router(clients_router)
app.include_router(agents_router)
app.include_router(stats_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
