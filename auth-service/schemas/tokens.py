from pydantic import BaseModel, EmailStr


class TokenData(BaseModel):
	email: EmailStr


class TokenRead(BaseModel):
	access_token: str
	token_type: str
