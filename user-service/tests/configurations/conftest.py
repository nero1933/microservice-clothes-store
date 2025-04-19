import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core import settings
from dependencies.db import get_async_session
from main import app
import models

DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_TEST_HOST = settings.DB_TEST_HOST
DB_NAME = settings.DB_NAME

# Test database URL
TEST_DATABASE_URL = (
	f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
	f"{settings.DB_TEST_HOST}:5432/{settings.DB_NAME}"
)

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
async_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="session")
async def test_prepare_database():
	print("Preparing database")
	async with test_engine.begin() as conn:
		await conn.run_sync(models.Base.metadata.drop_all)
		await conn.run_sync(models.Base.metadata.create_all)


@pytest_asyncio.fixture(loop_scope="function")
async def db():
	async with test_engine.begin() as conn:

		session = AsyncSession(bind=conn, expire_on_commit=False)

		try:
			yield session
		finally:
			await session.close()
			await conn.rollback()


@pytest_asyncio.fixture(loop_scope="function")
async def client(db):
	app.dependency_overrides[get_async_session] = lambda: db

	async with AsyncClient(
			transport=ASGITransport(app=app), base_url="http://test"
	) as real_client:
		wrapped_client = LoggingClient(real_client)
		yield wrapped_client

	app.dependency_overrides = {}


class LoggingClient:
	def __init__(self, client):
		self._client = client

	@staticmethod
	def print_response(response):
		print('-> response -> ')
		print('status_code: ', response.status_code)
		print('json: ', response.json())
		print()

	async def _wrap(self, method_name, *args, **kwargs):
		method = getattr(self._client, method_name)
		response = await method(*args, **kwargs)
		self.print_response(response)
		return response

	async def get(self, *args, **kwargs):
		return await self._wrap("get", *args, **kwargs)

	async def post(self, *args, **kwargs):
		return await self._wrap("post", *args, **kwargs)

	async def put(self, *args, **kwargs):
		return await self._wrap("put", *args, **kwargs)

	async def delete(self, *args, **kwargs):
		return await self._wrap("delete", *args, **kwargs)

	async def patch(self, *args, **kwargs):
		return await self._wrap("patch", *args, **kwargs)

	def __getattr__(self, item):
		return getattr(self._client, item)