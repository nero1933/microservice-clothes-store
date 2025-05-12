from abc import ABC, abstractmethod

from aio_pika import ExchangeType

from core.loggers import log
from core.messaging import MessagingMasterWorkerABC


class SendEmailWorker(MessagingMasterWorkerABC, ABC):
	# queue_name = 'email.send'

	# @classmethod
	# async def create_worker(cls, **kwargs) -> None:
	# 	queue_name = await cls.get_queue_name()
	# 	master = await cls.get_agent()
	#
	# 	exchange = await master.channel.declare_exchange(
	# 		"email_exchange", ExchangeType.TOPIC
	# 	)
	#
	# 	queue = await master.channel.declare_queue(queue_name)
	#
	# 	await queue.bind(exchange, routing_key="worker.email.send.reset")
	#
	# 	await master.create_worker(
	# 		queue_name=queue_name,
	# 		func=cls.callback,
	# 		**kwargs
	# 	)

	@staticmethod
	@abstractmethod
	async def send_mail(data: dict):
		raise NotImplementedError

	@classmethod
	async def callback(cls, data: dict, *args, **kwargs) -> dict | None:
		log.info(f'Received message (callback): {data}')
		await cls.send_mail(data)
		return data


class SendConfirmationEmailWorker(SendEmailWorker, ABC):

	@staticmethod
	async def build_conf_link(data: dict):
		log.info(f'Received message (send_mail): {data}')
