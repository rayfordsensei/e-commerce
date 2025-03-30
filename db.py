from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URI: str = config("DATABASE_URI")
DEBUG: bool = config("DEBUG", default=False, cast=bool)


engine: Engine = create_engine(url=DATABASE_URI)
SessionLocal: sessionmaker[Session] = sessionmaker[Session](bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
