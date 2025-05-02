from abc import ABC, abstractmethod

from core.messaging.base_agent import MessagingRPCFactoryABC


class MessagingRPCWorkerABC(MessagingRPCFactoryABC, ABC):

	@classmethod
	async def register(cls, **kwargs) -> None:
		queue_name = await cls.get_queue_name()
		rpc = await cls.get_agent()
		await rpc.register(
			method_name=queue_name,
			func=cls.callback,
			**kwargs
		)

	@staticmethod
	@abstractmethod
	async def callback(*args, **kwargs) -> dict:
		raise NotImplementedError


class MessagingRPCClientABC(MessagingRPCFactoryABC, ABC):

	@classmethod
	async def call(cls, **kwargs):
		rpc = await cls.get_agent()
		queue_name: str = await cls.get_queue_name()
		return await rpc.call(
			method_name=queue_name,
			kwargs=kwargs
		)
