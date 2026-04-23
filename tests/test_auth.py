import pytest
from sqlalchemy import select

from src.api.auth import create_token, decode_token, hash_password, verify_password
from src.api.models import Role, User


@pytest.mark.asyncio
async def test_login_success_sets_cookie(session_maker, client):
    async with session_maker() as session:
        session.add(
            User(
                nom="Agent",
                prenom="One",
                email="agent1@example.com",
                hashed_password=hash_password("secret123"),
                role=Role.agent,
            )
        )
        await session.commit()

    response = await client.post(
        "/api/auth/login",
        json={"email": "agent1@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "agent"
    assert "access_token=" in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_login_fails_with_bad_password(session_maker, client):
    async with session_maker() as session:
        session.add(
            User(
                nom="Agent",
                prenom="One",
                email="agent1@example.com",
                hashed_password=hash_password("secret123"),
                role=Role.agent,
            )
        )
        await session.commit()

    response = await client.post(
        "/api/auth/login",
        json={"email": "agent1@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Identifiants incorrects"


@pytest.mark.asyncio
async def test_protected_route_requires_cookie(client):
    response = await client.get("/api/clients/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_cookie(client):
    response = await client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "access_token=" in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_password_hash_and_verify():
    hashed = hash_password("strong-password")
    assert hashed != "strong-password"
    assert verify_password("strong-password", hashed) is True
    assert verify_password("wrong", hashed) is False


@pytest.mark.asyncio
async def test_create_and_decode_token(session_maker):
    async with session_maker() as session:
        user = User(
            nom="Patron",
            prenom="Boss",
            email="boss@example.com",
            hashed_password=hash_password("secret123"),
            role=Role.patron,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_token({"sub": str(user.id), "role": user.role, "nom": user.nom})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == str(user.id)

        db_user = (
            await session.execute(select(User).where(User.id == int(payload["sub"])))
        ).scalar_one_or_none()
        assert db_user is not None
