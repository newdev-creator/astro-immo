import asyncio
import argparse
import random
import sys

from faker import Faker
from sqlalchemy import delete, insert, select

from .auth import hash_password
from .database import SessionLocal, init_db
from .models import Bien, Client, Proprietaire, Role, StatutBien, TypeBien, User, achats


async def seed(force: bool = False):
    await init_db()
    async with SessionLocal() as db:
        if force:
            await db.execute(delete(achats))
            await db.execute(delete(Bien))
            await db.execute(delete(Client))
            await db.execute(delete(Proprietaire))
            await db.execute(delete(User))
            await db.commit()

        existing_patron = await db.scalar(
            select(User).where(User.email == "julien@immo.fr")
        )
        existing_bien = await db.scalar(select(Bien.id).limit(1))
        if existing_patron and existing_bien:
            print("Base deja peuplee, seed ignore")
            return

        fake = Faker("fr_FR")
        random.seed(42)
        Faker.seed(42)

        if not existing_patron:
            existing_patron = User(
                nom="Freisa",
                prenom="Julien",
                email="julien@immo.fr",
                hashed_password=hash_password("admin1234"),
                role=Role.patron,
            )
            db.add(existing_patron)
            await db.flush()

        agents = []
        for idx in range(1, 6):
            agent = User(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                email=f"agent{idx}@immo.fr",
                hashed_password=hash_password("agent1234"),
                role=Role.agent,
            )
            agents.append(agent)
        db.add_all(agents)
        await db.flush()

        proprietaires = []
        for _ in range(35):
            proprietaire = Proprietaire(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                email=fake.unique.email(),
                telephone=fake.phone_number(),
            )
            proprietaires.append(proprietaire)
        db.add_all(proprietaires)
        await db.flush()

        clients = []
        for _ in range(80):
            clients.append(
                Client(
                    nom=fake.last_name(),
                    prenom=fake.first_name(),
                    email=fake.unique.email(),
                    telephone=fake.phone_number(),
                    budget=round(random.uniform(70000, 900000), 2),
                    agent_id=random.choice(agents).id,
                )
            )
        db.add_all(clients)
        await db.flush()

        villes = [
            "Paris",
            "Lyon",
            "Marseille",
            "Bordeaux",
            "Toulouse",
            "Nantes",
            "Lille",
            "Nice",
        ]
        types = list(TypeBien)
        statuts = [StatutBien.disponible, StatutBien.vendu, StatutBien.loue]

        biens = []
        for _ in range(120):
            type_bien = random.choice(types)
            statut = random.choices(statuts, weights=[0.6, 0.25, 0.15], k=1)[0]
            surface = round(random.uniform(18, 260), 1)
            base_prix_m2 = random.uniform(1800, 7800)
            prix = round(surface * base_prix_m2, 2)
            ville = random.choice(villes)
            bien = Bien(
                titre=f"{type_bien.value.capitalize()} {fake.word().capitalize()} a {ville}",
                description=fake.paragraph(nb_sentences=4),
                prix=prix,
                surface=surface,
                ville=ville,
                adresse=fake.street_address(),
                type_bien=type_bien,
                statut=statut,
                image_url=None,
                agent_id=random.choice(agents).id,
                proprietaire_id=random.choice(proprietaires).id,
            )
            biens.append(bien)

        db.add_all(biens)
        await db.flush()

        clients_by_agent = {}
        for client in clients:
            clients_by_agent.setdefault(client.agent_id, []).append(client)

        ventes = 0
        achats_rows = []
        for bien in biens:
            if bien.statut != StatutBien.vendu:
                continue
            acheteurs_agent = clients_by_agent.get(bien.agent_id, [])
            if not acheteurs_agent:
                continue
            acheteur = random.choice(acheteurs_agent)
            achats_rows.append({"client_id": acheteur.id, "bien_id": bien.id})
            ventes += 1

        if achats_rows:
            await db.execute(insert(achats), achats_rows)

        await db.commit()
        print(
            "Seed termine: "
            f"1 patron, {len(agents)} agents, {len(proprietaires)} proprietaires, "
            f"{len(clients)} clients, {len(biens)} biens, {ventes} ventes."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Peuple la base de donnees")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Supprime les donnees actuelles avant de reseeder",
    )
    args = parser.parse_args()

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed(force=args.force))
