from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import User

SECRET_KEY = "change-moi-en-prod"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (jwt.PyJWTError, jwt.ExpiredSignatureError):
        return None


async def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    payload = decode_token(access_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token invalide")

    # We verify the user exists in the database
    user_id = payload.get("sub")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


async def require_patron(user: User = Depends(get_current_user)) -> User:
    if str(user.role) != "patron":
        raise HTTPException(status_code=403, detail="Accès réservé au patron")
    return user
