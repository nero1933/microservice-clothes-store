import aio_pika
import json

from fastapi import Depends

from core import settings
from dependencies import get_login_service


async def on_message(message: aio_pika.IncomingMessage, login_service=Depends(get_login_service)):
	async with message.process():
		data = json.loads(message.body)
		email = data["email"]
		password = data["password"]

		user = await login_service.authenticate(email, password)
		response = {"status": "ok", "user_id": user.id}

		await message.reply(
			aio_pika.Message(
				body=json.dumps(response).encode(),
				correlation_id=message.correlation_id,
			)
		)


async def main():
	connection = await aio_pika.connect_robust(settings.rabbitmq_url)
	channel = await connection.channel()
	queue = await channel.declare_queue("rpc_queue")
	await queue.consume(on_message)
	print("User service is listening...")


if __name__ == "__main__":
	import asyncio

	asyncio.run(main())
