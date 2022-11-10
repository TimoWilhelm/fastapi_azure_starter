from pydantic import BaseModel, constr

from app.models.meta import AllOptional


class SampleBase(BaseModel):
    name: constr(max_length=10)
    description: constr(max_length=100)


class SampleCreate(SampleBase):
    pass


class SampleUpdate(SampleBase, metaclass=AllOptional):
    pass


class Sample(SampleBase):
    id: int

    class Config:
        orm_mode = True
