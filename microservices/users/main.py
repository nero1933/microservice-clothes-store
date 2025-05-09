from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import settings
from core.cache.base_connection import BaseCacheConnection
from core.loggers import sql_logger

from api.v1 import users_router
from core.messaging import BaseMessagingConnection


@asynccontextmanager
async def lifespan(_: FastAPI):
	reddis = BaseCacheConnection()
	rabbitmq = BaseMessagingConnection()
	await reddis.setup_connection(settings.redis_url)
	await rabbitmq.setup_connection(settings.rabbitmq_url)
	yield
	await reddis.disconnect()
	await rabbitmq.disconnect()


app = FastAPI(
	lifespan=lifespan,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

app.include_router(users_router)

if __name__ == "__main__":
	uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
