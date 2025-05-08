from sqlalchemy.ext.asyncio import AsyncSession

from core.crud import mixins
from core.crud.base import BaseCRUD
from models import User

from core.messaging import MessagingMasterClientABC


class ForgotPasswordService(mixins.RetrieveModelMixin,
							BaseCRUD):
	model = User

	def __init__(self, db: AsyncSession):
		super().__init__(db)


class Temp(MessagingMasterClientABC):
	queue_name = 'worker.email.send'


