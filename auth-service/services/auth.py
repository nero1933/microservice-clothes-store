import json

from messaging.setup import RPCClient


class AuthService:

	async def login(self, username, password):
		rpc = await RPCClient().connect()
		data = {'username': username, 'password': password}
		response = await rpc.call(data)
		result = json.loads(response)
		return result