from abc import ABC, abstractmethod
from email.message import EmailMessage

from aio_pika import ExchangeType
import aiosmtplib

from config import settings
from core.loggers import log
from core.messaging import MessagingMasterWorkerABC


class SendEmailWorker(MessagingMasterWorkerABC, ABC):
	from_email: str = settings.DEFAULT_FROM_EMAIL
	smtp_host: str = settings.SMTP_HOST
	smtp_port: int = settings.SMTP_PORT

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

	@classmethod
	@abstractmethod
	async def get_email_message(cls, data: dict) -> EmailMessage:
		raise NotImplementedError

	@classmethod
	async def callback(cls, data: dict, *args, **kwargs) -> dict | None:
		log.info(f'Received message (callback): {data}')
		msg = await cls.get_email_message(data)
		await aiosmtplib.send(
			msg,
			hostname="postfix",
			port=587,
		)
		return {'status': 'ok'}


class SendConfirmationEmailWorker(SendEmailWorker, ABC):

	@staticmethod
	async def build_conf_link(data: dict):
		return data['reset_id']
