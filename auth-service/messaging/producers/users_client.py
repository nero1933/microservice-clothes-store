import json
from typing import Dict, Union

from .rpc import RPCClient


class UsersClient:
	@staticmethod
	async def get_auth_data(username: str, password: str) -> Dict[str, Union[str, bool]]:
		"""
		Sends 'username' & 'password' to users service to authenticate user.

		Returns a dictionary with:
		- 'user_id': a string representing the user ID (UUID).
		- 'permission': a boolean representing whether the user has permission (True/False).

		Response example: {'user_id': 'some uuid4 str', 'permission': True}
		"""

		rpc = await RPCClient().connect()
		data = {'username': username, 'password': password}
		response = await rpc.call(data, routing_key="rpc.users.get_auth_data")
		return json.loads(response)
