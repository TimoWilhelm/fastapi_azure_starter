from functools import cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


class Repository:
    def __init__(self, db: AsyncSession):
        self.db = db


@cache
def get_repository(repository: type[Repository]) -> Repository:
    def get(db: AsyncSession = Depends(get_db)) -> Repository:
        return repository(db)

    return get
