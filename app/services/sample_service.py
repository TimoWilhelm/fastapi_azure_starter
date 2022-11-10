from fastapi import Depends, HTTPException

from app.database.tables import SampleTable
from app.models.sample import SampleCreate, SampleUpdate
from app.repositories import get_repository
from app.repositories.sample_repository import SampleRepository


class SampleService:
    def __init__(self, repo: SampleRepository):
        self._repo = repo

    async def get(self):
        return await self._repo.get()

    async def get_by_id(self, id: int):
        result = await self._repo.get_by_id(id)
        if result is None:
            raise HTTPException(404, "Item not found")
        return result

    async def create(self, create: SampleCreate):
        item = SampleTable(**create.dict())
        return await self._repo.create(item)

    async def update(self, id: int, update: SampleUpdate):
        item = await self._repo.get_by_id(id)
        if item is None:
            raise HTTPException(404, "Item not found")
        for key, value in update.dict(exclude_unset=True).items():
            setattr(item, key, value)
        return await self._repo.update(item)

    async def delete(self, id: int):
        item = await self._repo.get_by_id(id)
        if item is None:
            raise HTTPException(404, "Item not found")
        await self._repo.delete(item)


def get_sample_service(
    sample_repo: SampleRepository = Depends(get_repository(SampleRepository)),
):
    return SampleService(sample_repo)
