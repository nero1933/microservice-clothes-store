from pydantic import BaseModel, EmailStr


class ForgotPassword(BaseModel):
	email: EmailStr