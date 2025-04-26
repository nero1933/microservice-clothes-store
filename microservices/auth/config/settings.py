from core.settings import Settings

class ServiceSettings(Settings):
	JWT_TOKEN_SECRET_KEY: str
	JWT_TOKEN_ALGORITHM: str
	ACCESS_TOKEN_EXPIRE_MINUTES: int
	REFRESH_TOKEN_EXPIRE_DAYS: int

settings = ServiceSettings()
