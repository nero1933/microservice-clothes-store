from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	DB_USER: str
	DB_PASSWORD: str
	DB_SOCKET: str
	DB_TEST_SOCKET: str
	DB_NAME: str

	RABBITMQ_USER: str
	RABBITMQ_PASSWORD: str
	RABBITMQ_SOCKET: str

	JWT_TOKEN_SECRET_KEY: str
	JWT_TOKEN_ALGORITHM: str
	ACCESS_TOKEN_EXPIRE_MINUTES: int
	REFRESH_TOKEN_EXPIRE_DAYS: int

	class Config:
		env_file = ".env"

	@property
	def db_url(self) -> str:
		return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SOCKET}/{self.DB_NAME}"

	@property
	def test_db_url(self) -> str:
		return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_TEST_SOCKET}/{self.DB_NAME}"

	@property
	def alembic_db_url(self) -> str:
		return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SOCKET}/{self.DB_NAME}"

	@property
	def rabbitmq_url(self) -> str:
		return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_SOCKET}/"


settings = Settings()
