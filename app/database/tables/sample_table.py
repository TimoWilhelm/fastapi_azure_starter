from sqlalchemy import Column, Integer, String

from app.database import Base


class SampleTable(Base):
    __tablename__ = "sample"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(10))
    description = Column(String(100))
