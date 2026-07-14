import os
from typing import AsyncGenerator
from sqlalchemy.pool import NullPool

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager

from app.core.config import get_settings
settings = get_settings()


pool_kwargs = {}
if os.getenv("TESTING") == "true":
    pool_kwargs["poolclass"] = NullPool
else:
    pool_kwargs["pool_pre_ping"] = True
    pool_kwargs["pool_size"] = 5

engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    echo=False,
    connect_args={"ssl": False},
    **pool_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def check_db_connection() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def transaction_scope(db: AsyncSession):
    if db.in_transaction():
        try:
            yield
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    else:
        async with db.begin():
            yield