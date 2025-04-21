# import aio_pika
# from core import settings  # Импортируй настройки как тебе удобно
#
# _connection: aio_pika.RobustConnection | None = None
#
# async def get_connection() -> aio_pika.RobustConnection:
#     global _connection
#     if _connection is None or _connection.is_closed:
#         _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
#     return _connection
#
# async def get_channel() -> aio_pika.Channel:
#     connection = await get_connection()
#     return await connection.channel()