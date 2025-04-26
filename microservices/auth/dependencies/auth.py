from api.v1.services import AuthService


def get_auth_service() -> AuthService:
	return AuthService()