from sqlalchemy.ext.asyncio import AsyncSession


class Repository:
    def __init__(self, db: AsyncSession):
        self.db = db
