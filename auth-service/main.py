from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.v1 import auth_router
from messaging.connection_manager import rabbitmq


@asynccontextmanager
async def lifespan(_: FastAPI):
	await rabbitmq.connect()
	yield
	await rabbitmq.disconnect()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)

if __name__ == "__main__":
	uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
