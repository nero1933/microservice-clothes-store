from abc import abstractmethod, ABC

from aio_pika.patterns import RPC

from core.messaging import BaseMessagingConnection
from ..loggers import log


class RPCCreator(BaseMessagingConnection, ABC):
	_rpc: RPC | None = None

	@classmethod
	async def _create_rpc(cls) -> RPC:
		channel = await cls.get_channel()
		cls._rpc = await RPC.create(channel)
		return cls._rpc

	@classmethod
	async def get_rpc(cls) -> RPC:
		if cls._rpc is None:
			return await cls._create_rpc()

		return cls._rpc


class RPCSingleton(ABC):
	_instances = {}

	def __new__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super().__new__(cls)

		return cls._instances[cls]


class RPCWorkerABC(RPCSingleton, RPCCreator, ABC):
	_method_name: str | None = None

	@classmethod
	async def register(cls, *args, **kwargs) -> None:
		if cls._method_name is None:
			error = 'cls._method_name is None'
			log.error(error)
			raise ValueError(error)

		rpc = await cls.get_rpc()
		await rpc.register(
			method_name=cls._method_name,
			func=cls.callback,
			**kwargs
		)

	@staticmethod
	@abstractmethod
	async def callback(*args, **kwargs) -> dict:
		pass


class RPCClientABC(RPCSingleton, RPCCreator, ABC):
	@classmethod
	@abstractmethod
	async def call(cls, *args, **kwargs):
		pass
