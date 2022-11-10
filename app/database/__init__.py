from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app import settings

Base = declarative_base()

engine = create_async_engine(settings.POSTGRES_CONNECTION_STRING)


async def get_db():
    async with AsyncSession(
        engine, expire_on_commit=False, autocommit=False, autoflush=False
    ) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
        finally:
            await session.close()
