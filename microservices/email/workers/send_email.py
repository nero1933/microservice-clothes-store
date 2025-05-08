from aio_pika import ExchangeType

from core.loggers import log
from core.messaging import MessagingMasterWorkerABC


class SendEmailWorker(MessagingMasterWorkerABC):
	queue_name = 'worker.email.send'

	@classmethod
	async def create_worker(cls, **kwargs) -> None:
		queue_name = await cls.get_queue_name()
		master = await cls.get_agent()

		exchange = await master.channel.declare_exchange(
			"email_exchange", ExchangeType.TOPIC
		)

		queue = await master.channel.declare_queue(queue_name)

		await queue.bind(exchange, routing_key="worker.email.send.reset")

		await master.create_worker(
			queue_name=queue_name,
			func=cls.callback,
			**kwargs
		)

	@staticmethod
	async def callback(d: dict) -> dict:
		log.info(f'---> EMAIL WORKER RECEIVED: {d}')
		return d
