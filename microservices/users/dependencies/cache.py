from redis.asyncio import Redis

from core.cache.base_connection import BaseCacheConnection


async def get_forgot_password_service() -> Redis:
	return await BaseCacheConnection.get_connection()
