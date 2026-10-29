from collections.abc import Generator

from sqlalchemy.orm import Session

from taskflow_api.db.database import session_factory


def get_db() -> Generator[Session]:
    db: Session = session_factory()
    try:
        yield db
    finally:
        db.close()
