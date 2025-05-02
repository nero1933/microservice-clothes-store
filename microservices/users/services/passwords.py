from sqlalchemy.ext.asyncio import AsyncSession

from core.crud import mixins
from core.crud.base import BaseCRUD
from models import User


class ForgotPasswordService(mixins.RetrieveModelMixin,
							BaseCRUD):
	model = User

	def __init__(self, db: AsyncSession):
		super().__init__(db)