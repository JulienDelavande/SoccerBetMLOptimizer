# db/base.py
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

# Noms stables pour éviter le churn dans Alembic
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "%(table_name)s_pkey",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

if (DB_TYPE := os.getenv('DB_TYPE')) is None:
    raise ValueError("Missing environment variable: DB_TYPE")
if (DB_PILOT := os.getenv('DB_PILOT')) is None:
    raise ValueError("Missing environment variable: DB_PILOT")
if (DB_USER := os.getenv("DB_USER")) is None:
    raise ValueError("Missing environment variable: DB_USER")
if (DB_PASSWORD := os.getenv("DB_PASSWORD")) is None:
    raise ValueError("Missing environment variable: DB_PASSWORD")
if (DB_HOST := os.getenv("DB_HOST")) is None:
    raise ValueError("Missing environment variable: DB_HOST")
if (DB_PORT := os.getenv("DB_PORT")) is None:
    raise ValueError("Missing environment variable: DB_PORT")
if (DB_NAME := os.getenv("DB_NAME")) is None:
    raise ValueError("Missing environment variable: DB_NAME")
DB_URL = f'{DB_TYPE}+{DB_PILOT}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
