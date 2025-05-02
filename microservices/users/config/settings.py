from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	DB_USER: str
	DB_PASSWORD: str
	DB_SOCKET: str
	DB_TEST_SOCKET: str
	DB_NAME: str

	RABBITMQ_NAME: str
	RABBITMQ_USER: str
	RABBITMQ_PASSWORD: str
	RABBITMQ_SOCKET: str

	RESET_PASSWORD_KEY_FORMAT: str | None = None
	RESET_PASSWORD_KEY_TIMEOUT: int | None = None

	RESET_PASSWORD_COUNTER_FORMAT: str | None = None
	RESET_PASSWORD_COUNTER_TIMEOUT: int | None = None

	RESET_PASSWORD_MAX_ATTEMPTS: int | None = None

	class Config:
		env_file = ".env"

	@property
	def db_url(self) -> str:
		return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
				f"{self.DB_SOCKET}/{self.DB_NAME}")

	@property
	def test_db_url(self) -> str:
		return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
				f"{self.DB_TEST_SOCKET}/{self.DB_NAME}")

	@property
	def alembic_db_url(self) -> str:
		return (f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
				f"{self.DB_SOCKET}/{self.DB_NAME}")

	@property
	def rabbitmq_url(self) -> str:
		return (f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@"
				f"{self.RABBITMQ_SOCKET}/?name={self.RABBITMQ_NAME}")

	@property
	def redis_url(self) -> str:
		return "redis://users-redis:6379/1"


settings = Settings()