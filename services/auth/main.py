from contextlib import asynccontextmanager

import uvicorn
from aio_pika.patterns import RPC
from fastapi import FastAPI

from api.v1 import auth_router
from config import settings
from core.messaging import BaseMessagingConnection
# from services.users.worker import authenticate



@asynccontextmanager
async def lifespan(_: FastAPI):
	rabbitmq = BaseMessagingConnection()
	await rabbitmq.setup_connection(settings.rabbitmq_url)
	yield
	await rabbitmq.disconnect()


app = FastAPI(lifespan=lifespan)
# app = FastAPI()
app.include_router(auth_router)

if __name__ == "__main__":
	uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
