from .db_config import engine

from .db_config import AsyncSessionLocal


async def get_async_session():
	# async with engine.begin() as connection:
	# 	await connection.run_sync(Base.metadata.create_all)

	db = AsyncSessionLocal()
	try:
		yield db
	finally:
		await db.close()