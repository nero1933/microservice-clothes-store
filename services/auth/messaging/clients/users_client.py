import json
from typing import Dict

from loggers import default_logger
from .rpc import rpc_client


class UsersClient:
	@staticmethod
	async def get_auth_data(username: str, password: str) -> Dict[str, str]:
		"""
		Sends 'username' & 'password' to users service to authenticate user.

		Returns a dictionary with:
		- 'user_id': a string representing the user ID (UUID).
		   or
		- 'error': a string representing the error message.

		Response example: {'user_id': 'some uuid4 str'}
		"""

		client = await rpc_client.setup()
		data = {'username': username, 'password': password}
		response = await client.call(data, routing_key="rpc.users.get_auth_data")
		result = json.loads(response)
		default_logger.info(f'[✓] Response from users-service: -> {result}')
		return result
