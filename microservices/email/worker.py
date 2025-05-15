import asyncio
import signal
from aiosmtplib import SMTP

from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

from config import settings
from core.messaging import MessagingConnection
from core.loggers import log
from smtp_connection.smtp_connection import SmtpConnection
from workers import SendResetPasswordEmailWorker

shutdown_event = asyncio.Event()


def shutdown():
	log.info("Shutdown signal received.")
	shutdown_event.set()


async def main():
	workers = (SendResetPasswordEmailWorker,)
	rabbit = MessagingConnection()
	smtp = SmtpConnection()

	await rabbit.setup_connection(settings.rabbitmq_url)
	await smtp.setup_connection()

	for worker in workers:
		await worker.create_worker()

	loop = asyncio.get_running_loop()
	loop.add_signal_handler(signal.SIGINT, shutdown)
	loop.add_signal_handler(signal.SIGTERM, shutdown)

	try:
		await shutdown_event.wait()
	finally:
		log.info("Shutting down gracefully...")
		await smtp.disconnect()
		await rabbit.disconnect()


if __name__ == "__main__":
	log.info("Worker started")
	asyncio.run(main())
