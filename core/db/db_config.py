from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core import settings

engine = create_async_engine(settings.db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
