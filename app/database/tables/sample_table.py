from datetime import datetime

from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SampleTable(Base):
    __tablename__ = "sample"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String[100], nullable=True)
    create_date: Mapped[datetime] = mapped_column(insert_default=func.now())
