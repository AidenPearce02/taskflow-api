from collections.abc import Generator

from sqlalchemy.orm import Session

from taskflow_api.db.database import SessionLocal


def get_db() -> Generator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
