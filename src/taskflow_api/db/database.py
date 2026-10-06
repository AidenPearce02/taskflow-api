from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from taskflow_api.core.config import settings

engine = create_engine(settings.db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
