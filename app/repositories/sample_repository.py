from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.tables import SampleTable
from app.repositories import Repository


class SampleRepository(Repository):
    async def get(self, skip: int = 0, limit: int = 100) -> list[SampleTable]:
        query = select(SampleTable).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, id: int) -> SampleTable | None:
        return await self.db.get(SampleTable, id)

    async def create(self, item: SampleTable) -> SampleTable:
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update(self, item: SampleTable) -> SampleTable:
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, item: SampleTable):
        await self.db.delete(item)
        await self.db.commit()


def get_sample_repository(db: AsyncSession = Depends(get_db)):
    return SampleRepository(db)
