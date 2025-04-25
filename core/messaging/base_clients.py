# import asyncio
# import uuid
# from abc import ABC
# from asyncio import Future, get_event_loop
#
# from aio_pika import Message
# from aio_pika.abc import AbstractExchange, AbstractIncomingMessage
#
# from core.messaging import BaseMessagingExchange, BaseMessagingQueue
# from loggers import default_logger
#
#
# class BaseMessagingClient(BaseMessagingExchange, ABC):
# 	def __init__(
# 			self,
# 			message_kwargs: dict | None = None,
# 			publish_kwargs: dict | None = None,
# 			**kwargs
# 	) -> None:
# 		super().__init__(**kwargs)
# 		self._message_kwargs: dict = message_kwargs or {'content_type': 'application/json'}
# 		self._publish_kwargs: dict = publish_kwargs or {}
#
# 	async def publish(self, body: bytes, routing_key: str) -> None:
# 		try:
# 			exchange: AbstractExchange = await self.get_exchange()
# 			message = Message(body, **self._message_kwargs)
# 			await exchange.publish(message, routing_key=routing_key, **self._publish_kwargs)
# 			default_logger.info(
# 				f"[x] Published message to '{exchange.name}' with routing_key='{routing_key}'"
# 			)
# 		except Exception as e:
# 			default_logger.error(
# 				f"[!] Failed to publish message: {e}"
# 			)
# 			raise e
#
#
# class BaseMessagingRPCClient(BaseMessagingQueue, ABC):
# 	def __init__(
# 			self,
# 			message_kwargs: dict | None = None,
# 			publish_kwargs: dict | None = None,
# 			consume_kwargs: dict | None = None,
# 			**kwargs
# 	) -> None:
# 		super().__init__(**kwargs)
# 		self._futures: dict[str, Future] = {}
# 		self._message_kwargs: dict = message_kwargs or {'application/msgpack'}
# 		self._publish_kwargs: dict = publish_kwargs or {}
# 		self._consume_kwargs: dict = consume_kwargs or {'no_ack': True}
#
# 	async def _on_response(self, message: AbstractIncomingMessage):
# 		correlation_id = message.correlation_id
# 		if correlation_id in self._futures:
# 			future = self._futures.pop(correlation_id)
# 			future.set_result(message.body)
#
# 	async def call(self, body: bytes, routing_key: str, timeout: float = 5.0) -> bytes:
# 		correlation_id = str(uuid.uuid4())
# 		loop = get_event_loop()
# 		future = loop.create_future()
# 		self._futures[correlation_id] = future
#
# 		callback_queue = await self.get_queue()
# 		consumer_tag = await callback_queue.consume(self._on_response, **self._consume_kwargs)
#
# 		message = Message(
# 			body,
# 			correlation_id=correlation_id,
# 			reply_to=callback_queue.name,
# 			**self._message_kwargs,
# 		)
#
# 		exchange = await self.get_exchange()
# 		await exchange.publish(message, routing_key=routing_key, **self._publish_kwargs)
# 		default_logger.info(f"[X] Sent RPC message with correlation_id={correlation_id}")
#
# 		try:
# 			result = await asyncio.wait_for(future, timeout)
# 		finally:
# 			await callback_queue.cancel(consumer_tag)
# 			await callback_queue.delete()
#
# 		return result
