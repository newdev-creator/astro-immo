import enum

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# Table d'association Client <-> Bien (achats)
achats = Table(
    "achats",
    Base.metadata,
    Column("client_id", Integer, ForeignKey("clients.id")),
    Column("bien_id", Integer, ForeignKey("biens.id")),
)


class Role(str, enum.Enum):
    patron = "patron"
    agent = "agent"


class StatutBien(str, enum.Enum):
    disponible = "disponible"
    vendu = "vendu"
    loue = "loue"


class TypeBien(str, enum.Enum):
    appartement = "appartement"
    maison = "maison"
    terrain = "terrain"
    commercial = "commercial"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), default=Role.agent)

    biens = relationship("Bien", back_populates="agent")
    clients = relationship("Client", back_populates="agent")


class Proprietaire(Base):
    __tablename__ = "proprietaires"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True)
    telephone = Column(String)

    biens = relationship("Bien", back_populates="proprietaire")


class Bien(Base):
    __tablename__ = "biens"
    id = Column(Integer, primary_key=True)
    titre = Column(String, nullable=False)
    description = Column(String)
    prix = Column(Float, nullable=False)
    surface = Column(Float)
    ville = Column(String)
    adresse = Column(String)
    type_bien = Column(Enum(TypeBien), default=TypeBien.appartement)
    statut = Column(Enum(StatutBien), default=StatutBien.disponible)
    image_url = Column(String)  # URL Cloudinary

    agent_id = Column(Integer, ForeignKey("users.id"))
    agent = relationship("User", back_populates="biens")

    proprietaire_id = Column(Integer, ForeignKey("proprietaires.id"))
    proprietaire = relationship("Proprietaire", back_populates="biens")

    acheteurs = relationship("Client", secondary=achats, back_populates="achats")


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True)
    telephone = Column(String)
    budget = Column(Float)

    agent_id = Column(Integer, ForeignKey("users.id"))
    agent = relationship("User", back_populates="clients")

    achats = relationship("Bien", secondary=achats, back_populates="acheteurs")
