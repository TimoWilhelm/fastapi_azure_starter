from functools import cache
from typing import Callable

from fastapi import Depends
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import Settings, get_settings

Base = declarative_base()


@cache
def session_factory(connection_string: str):
    engine = create_async_engine(
        connection_string,
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

    async_session: Callable[..., AsyncSession] = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    return async_session


async def get_db(settings: Settings = Depends(get_settings)):
    create_async_session = session_factory(settings.POSTGRES_CONNECTION_STRING)
    async with create_async_session() as session:
        yield session
