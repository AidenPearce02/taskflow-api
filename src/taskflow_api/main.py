from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text

from taskflow_api.db.database import Session, get_db

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
def get_db(db: Annotated[Session, Depends(get_db)]):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": e}
