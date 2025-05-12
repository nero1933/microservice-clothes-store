from abc import ABC, abstractmethod

from core.loggers import log
from core.messaging.base_agent import MessagingMasterFactoryABC


class MessagingMasterWorkerABC(MessagingMasterFactoryABC, ABC):

	@classmethod
	async def create_worker(cls, *args, **kwargs) -> None:
		queue_name = await cls.get_queue_name()
		master = await cls.get_agent()
		await master.create_worker(
			queue_name=queue_name,
			func=cls.callback,
			**kwargs
		)

	@classmethod
	@abstractmethod
	async def callback(cls, *args, **kwargs) -> dict:
		raise NotImplementedError


class MessagingMasterClientABC(MessagingMasterFactoryABC, ABC):

	@classmethod
	async def create_task(cls, *args, **kwargs):
		try:
			master = await cls.get_agent()
			queue_name: str = await cls.get_queue_name()
			return await master.create_task(
				channel_name=queue_name,
				kwargs=kwargs,
			)
		except Exception as e:
			log.warning(e)
