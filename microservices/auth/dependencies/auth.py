from services import AuthService


def get_auth_service() -> AuthService:
	return AuthService()