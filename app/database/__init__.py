from typing import Callable

from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app import settings

Base = declarative_base()

engine = create_async_engine(
    settings.POSTGRES_CONNECTION_STRING,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30.0,
    pool_recycle=1800,  # 30 minutes
    pool_pre_ping=True,
    pool_use_lifo=True,  # https://docs.sqlalchemy.org/en/14/core/pooling.html#pool-use-lifo
)

SQLAlchemyInstrumentor().instrument(
    engine=engine.sync_engine,
    enable_commenter=True,
)

async_session: Callable[..., AsyncSession] = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
        finally:
            await session.close()
