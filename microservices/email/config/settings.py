from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	RABBITMQ_NAME: str
	RABBITMQ_USER: str
	RABBITMQ_PASSWORD: str
	RABBITMQ_SOCKET: str

	class Config:
		env_file = ".env"

	@property
	def rabbitmq_url(self) -> str:
		return (f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@"
				f"{self.RABBITMQ_SOCKET}/?name={self.RABBITMQ_NAME}")
