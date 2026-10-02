from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.conf.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# create_engine creates pool of connections with Postgres database
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI routes (the session is closed automatically after the query)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
