from abc import ABC, abstractmethod

from aio_pika.patterns import RPC, Master

from core.loggers import log
from core.messaging import BaseMessagingConnection


class MessagingAgentFactoryABC(BaseMessagingConnection, ABC):
	_agent = None
	queue_name: str | None = None

	@classmethod
	@abstractmethod
	async def _create_agent(cls):
		raise NotImplementedError

	@classmethod
	async def get_agent(cls):
		if cls._agent:
			return cls._agent

		return await cls._create_agent()

	@classmethod
	async def get_queue_name(cls):
		if cls.queue_name:
			return cls.queue_name

		log.error(f'{cls.__name__} Queue name is not set')
		raise ValueError(
			f"{cls.__name__}: Queue name must be defined before calling get_queue_name()"
		)


class MessagingRPCFactoryABC(MessagingAgentFactoryABC, ABC):
	_agent: RPC | None = None

	@classmethod
	async def _create_agent(cls) -> RPC:
		channel = await cls.get_channel()
		cls._agent = await RPC.create(channel)
		return cls._agent


class MessagingMasterFactoryABC(MessagingAgentFactoryABC, ABC):
	_agent: Master | None = None

	@classmethod
	async def _create_agent(cls) -> Master:
		channel = await cls.get_channel()
		cls._agent = Master(channel)
		return cls._agent
