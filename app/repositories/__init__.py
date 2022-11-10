from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


class Repository:
    def __init__(self, db: AsyncSession):
        self.db = db


def get_repository(repository: type[Repository]):
    def get_repository_internal(db: AsyncSession = Depends(get_db)):
        return repository(db)

    return get_repository_internal
