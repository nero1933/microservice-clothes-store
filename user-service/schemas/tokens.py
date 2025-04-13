from pydantic import BaseModel, EmailStr


class TokenDataSchema(BaseModel):
    email: EmailStr


class TokenReadSchema(BaseModel):
    access_token: str
    token_type: str
