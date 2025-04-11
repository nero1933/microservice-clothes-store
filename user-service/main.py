from loggers import sql_logger
import uvicorn
from fastapi import FastAPI

from endpoints.auth import router as users_router

app = FastAPI()

app.include_router(users_router)


if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
