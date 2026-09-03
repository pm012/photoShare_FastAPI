from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.conf.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# create_engine створює пулл з'єднань з нашою PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency для роутів FastAPI (автоматично закриває сесію після запиту)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
