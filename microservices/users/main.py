import uvicorn
from fastapi import FastAPI
from core.loggers import sql_logger
# from prometheus_fastapi_instrumentator import Instrumentator

from api.v1 import users_router

app = FastAPI(
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

app.include_router(users_router)

# Instrumentator().instrument(app).expose(app)

if __name__ == "__main__":
	uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
