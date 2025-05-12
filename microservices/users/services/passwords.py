# from typing import Optional
#
# from pydantic import BaseModel
# from sqlalchemy import select, Row
# from sqlalchemy.ext.asyncio import AsyncSession
#
# import schemas
# from core.crud import mixins
# from core.crud.base import BaseCRUD
# from core.loggers import log
# from models import User

# from core.messaging import MessagingMasterClientABC


# class ForgotPasswordService(mixins.RetrieveModelMixin,
# 							BaseCRUD):
# 	model = User
# 	schema = schemas.UserForgotPassword
# 	lookup_field = 'email'
#
# 	def __init__(self, db: AsyncSession):
# 		super().__init__(db)
#
#
# 	async def get_object(self, value) -> Row | None:
# 		stmt = select(self.model.id, self.model.email) \
# 			.where(getattr(self.model, self.lookup_field) == value)
# 		result = await self.db.execute(stmt)
# 		rows = result.all()
# 		if not rows:
# 			return None
#
# 		if len(rows) > 1:
# 			error_message = f"More than one record found for {value}"
# 			log.info(error_message)
# 			raise ValueError(error_message)
#
# 		return rows[0]
# 		# return schemas.UserForgotPassword(id=row.id, email=row.email)


# class Temp(MessagingMasterClientABC):
# 	queue_name = 'email.send.reset_password'
