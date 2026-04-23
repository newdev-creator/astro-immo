import pytest

from src.api.auth import create_token, hash_password
from src.api.models import Bien, Client, Role, StatutBien, TypeBien, User


def _auth_header(user_id: int, role: str, nom: str):
    token = create_token({"sub": str(user_id), "role": role, "nom": nom})
    return {"cookie": f"access_token={token}"}


async def _seed_full_dataset(session_maker):
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
                Client(
                    nom="Client",
                    prenom="Alpha",
                    email="client.alpha@example.com",
                    budget=150000,
                    agent_id=agent1.id,
                ),
                Client(
                    nom="Client",
                    prenom="Beta",
                    email="client.beta@example.com",
                    budget=400000,
                    agent_id=agent2.id,
                ),
            ]
        )

        session.add_all(
            [
                Bien(
                    titre="A1 dispo",
                    prix=100000,
                    type_bien=TypeBien.appartement,
                    statut=StatutBien.disponible,
                    agent_id=agent1.id,
                ),
                Bien(
                    titre="A1 vendu",
                    prix=180000,
                    type_bien=TypeBien.maison,
                    statut=StatutBien.vendu,
                    agent_id=agent1.id,
                ),
                Bien(
                    titre="A2 dispo",
                    prix=220000,
                    type_bien=TypeBien.terrain,
                    statut=StatutBien.disponible,
                    agent_id=agent2.id,
                ),
            ]
        )

        await session.commit()
        return patron.id, agent1.id, agent2.id


@pytest.mark.asyncio
async def test_clients_list_is_scoped_for_agent(session_maker, client):
    _, agent1_id, _ = await _seed_full_dataset(session_maker)
    response = await client.get(
        "/api/clients/",
        headers=_auth_header(agent1_id, "agent", "Agent One"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["agent_id"] == agent1_id


@pytest.mark.asyncio
async def test_client_access_forbidden_between_agents(session_maker, client):
    _, agent1_id, agent2_id = await _seed_full_dataset(session_maker)
    list_response = await client.get(
        "/api/clients/",
        headers=_auth_header(agent2_id, "agent", "Agent Two"),
    )
    foreign_client_id = list_response.json()[0]["id"]

    response = await client.get(
        f"/api/clients/{foreign_client_id}",
        headers=_auth_header(agent1_id, "agent", "Agent One"),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_patron_lists_all_clients(session_maker, client):
    patron_id, _, _ = await _seed_full_dataset(session_maker)
    response = await client.get(
        "/api/clients/",
        headers=_auth_header(patron_id, "patron", "Patron Boss"),
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_create_client_assigns_current_agent(session_maker, client):
    _, agent1_id, _ = await _seed_full_dataset(session_maker)
    response = await client.post(
        "/api/clients/",
        headers=_auth_header(agent1_id, "agent", "Agent One"),
        json={
            "nom": "Client",
            "prenom": "Nouveau",
            "email": "client.nouveau@example.com",
            "budget": 210000,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["agent_id"] == agent1_id


@pytest.mark.asyncio
async def test_non_patron_cannot_list_agents(session_maker, client):
    _, agent1_id, _ = await _seed_full_dataset(session_maker)
    response = await client.get(
        "/api/agents/",
        headers=_auth_header(agent1_id, "agent", "Agent One"),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_patron_cannot_create_agent_with_duplicate_email(session_maker, client):
    patron_id, _, _ = await _seed_full_dataset(session_maker)
    response = await client.post(
        "/api/agents/",
        headers=_auth_header(patron_id, "patron", "Patron Boss"),
        json={
            "nom": "Dup",
            "prenom": "Agent",
            "email": "agent1@example.com",
            "password": "secret123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email déjà utilisé"


@pytest.mark.asyncio
async def test_patron_cannot_delete_self(session_maker, client):
    patron_id, _, _ = await _seed_full_dataset(session_maker)
    response = await client.delete(
        f"/api/agents/{patron_id}",
        headers=_auth_header(patron_id, "patron", "Patron Boss"),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Impossible de se supprimer soi-même"


@pytest.mark.asyncio
async def test_stats_for_agent_only_counts_own_data(session_maker, client):
    _, agent1_id, _ = await _seed_full_dataset(session_maker)
    response = await client.get(
        "/api/stats/",
        headers=_auth_header(agent1_id, "agent", "Agent One"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["biens_total"] == 2
    assert payload["biens_disponibles"] == 1
    assert payload["biens_vendus"] == 1
    assert payload["clients_total"] == 1


@pytest.mark.asyncio
async def test_stats_for_patron_counts_global_data(session_maker, client):
    patron_id, _, _ = await _seed_full_dataset(session_maker)
    response = await client.get(
        "/api/stats/",
        headers=_auth_header(patron_id, "patron", "Patron Boss"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["biens_total"] == 3
    assert payload["biens_disponibles"] == 2
    assert payload["biens_vendus"] == 1
    assert payload["clients_total"] == 2
