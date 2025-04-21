from contextlib import asynccontextmanager

import aio_pika
import uvicorn
# from loggers import log_sql_query
from fastapi import FastAPI

from api.v1 import auth_router
from core import settings


# async def lifespan(app: FastAPI):
# 	await rpc.connect()
# 	yield
# 	await rpc.connection.close()
#

app = FastAPI()
app.include_router(auth_router)

if __name__ == "__main__":
	uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
