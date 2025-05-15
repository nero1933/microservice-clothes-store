from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from .users import UserPassword


class ForgotPassword(BaseModel):
	email: EmailStr


class UserForgotPassword(ForgotPassword):
	id: UUID


class ResetPassword(UserPassword):
	confirm_password: str

	@model_validator(mode='after')
	def passwords_match(cls, model):
		if model.password != model.confirm_password:
			raise ValueError('Passwords do not match')

		return model


