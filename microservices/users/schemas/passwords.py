from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, model_validator


class ForgotPassword(BaseModel):
	email: EmailStr


class UserForgotPassword(ForgotPassword):
	id: UUID


class ResetPassword(BaseModel):
	password: str
	confirm_password: str

	@field_validator('password')
	def password_validator(cls, value):
		if len(value) < 8:
			raise ValueError('Password must be at least 8 characters')

		if value != value.strip():
			raise ValueError('Password must not start or end with spaces')

		return value


	@model_validator(mode='after')
	def passwords_match(cls, model):
		if model.password != model.confirm_password:
			raise ValueError('Passwords do not match')

		return model


