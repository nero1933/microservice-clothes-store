from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection
from core import settings


class RabbitMQManager:
    def __init__(self):
        self._connection: AbstractConnection | None = None

    async def connect(self):
        if not self._connection:
            self._connection = await connect_robust(settings.rabbitmq_url)

        return self._connection

    async def get_connection(self) -> AbstractConnection:
        if not self._connection:
            await self.connect()

        return self._connection

    async def create_channel(self) -> AbstractChannel:
        connection = await self.get_connection()
        return await connection.channel()

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()


# singleton
rabbitmq = RabbitMQManager()