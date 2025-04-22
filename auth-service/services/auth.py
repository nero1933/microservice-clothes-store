from typing import Dict, Union

from messaging.producers import UsersClient


class AuthService:

	@staticmethod
	async def authenticate(username: str, password: str) -> Dict[str, Union[str, bool]]:
		"""
		Sends 'username' & 'password' to users service to authenticate user.

		Returns a dictionary with:
        - 'user_id': a string representing the user ID (UUID).
        - 'permission': a boolean representing whether the user has permission (True/False).

		Response example: {'user_id': 'some uuid4 str', 'permission': True}
		"""
		return await UsersClient.get_auth_data(username, password)
