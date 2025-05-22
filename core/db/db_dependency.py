from contextlib import asynccontextmanager

from .db_config import AsyncSessionLocal

@asynccontextmanager
async def get_async_session():
	# async with engine.begin() as connection:
	# 	await connection.run_sync(Base.metadata.create_all)

	# db = AsyncSessionLocal()
	# try:
	# 	yield db
	# finally:
	# 	await db.close()

	async with AsyncSessionLocal() as db:
		yield db
