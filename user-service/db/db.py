from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base

from core import settings

DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_HOST = settings.DB_HOST
DB_NAME = settings.DB_NAME

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def async_get_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


def get_db():
    pass
