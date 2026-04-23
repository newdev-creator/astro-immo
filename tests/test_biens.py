import pytest

from src.api.auth import create_token, hash_password
from src.api.models import Bien, Role, StatutBien, TypeBien, User


async def _seed_users_and_biens(session_maker):
    async with session_maker() as session:
        patron = User(
            nom="Patron",
            prenom="Boss",
            email="patron@example.com",
            hashed_password=hash_password("secret123"),
            role=Role.patron,
        )
        agent1 = User(
            nom="Agent",
            prenom="One",
            email="agent1@example.com",
            hashed_password=hash_password("secret123"),
            role=Role.agent,
        )
        agent2 = User(
            nom="Agent",
            prenom="Two",
            email="agent2@example.com",
            hashed_password=hash_password("secret123"),
            role=Role.agent,
        )
        session.add_all([patron, agent1, agent2])
        await session.flush()

        session.add_all(
            [
                Bien(
                    titre="Studio centre",
                    prix=120000,
                    type_bien=TypeBien.appartement,
                    statut=StatutBien.disponible,
                    ville="Paris",
                    agent_id=agent1.id,
                ),
                Bien(
                    titre="Maison vendue",
                    prix=250000,
                    type_bien=TypeBien.maison,
                    statut=StatutBien.vendu,
                    ville="Lyon",
                    agent_id=agent1.id,
                ),
                Bien(
                    titre="Terrain agent2",
                    prix=90000,
                    type_bien=TypeBien.terrain,
                    statut=StatutBien.disponible,
                    ville="Bordeaux",
                    agent_id=agent2.id,
                ),
            ]
        )
        await session.commit()
        return patron.id, agent1.id, agent2.id


def _auth_cookie_header(user_id: int, role: str, nom: str):
    token = create_token({"sub": str(user_id), "role": role, "nom": nom})
    return {"cookie": f"access_token={token}"}


@pytest.mark.asyncio
async def test_list_public_biens_returns_only_disponibles(session_maker, client):
    await _seed_users_and_biens(session_maker)
    response = await client.get("/api/biens/publics")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert all(item["statut"] == "disponible" for item in payload)


@pytest.mark.asyncio
async def test_agent_lists_only_his_biens(session_maker, client):
    _, agent1_id, _ = await _seed_users_and_biens(session_maker)
    response = await client.get(
        "/api/biens/",
        headers=_auth_cookie_header(agent1_id, "agent", "Agent One"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert all(item["agent_id"] == agent1_id for item in payload)


@pytest.mark.asyncio
async def test_patron_lists_all_biens(session_maker, client):
    patron_id, _, _ = await _seed_users_and_biens(session_maker)
    response = await client.get(
        "/api/biens/",
        headers=_auth_cookie_header(patron_id, "patron", "Patron Boss"),
    )

    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_agent_cannot_access_other_agent_bien(session_maker, client):
    _, agent1_id, agent2_id = await _seed_users_and_biens(session_maker)
    list_response = await client.get(
        "/api/biens/",
        headers=_auth_cookie_header(agent2_id, "agent", "Agent Two"),
    )
    foreign_bien_id = list_response.json()[0]["id"]

    response = await client.get(
        f"/api/biens/{foreign_bien_id}",
        headers=_auth_cookie_header(agent1_id, "agent", "Agent One"),
    )
    assert response.status_code == 403
