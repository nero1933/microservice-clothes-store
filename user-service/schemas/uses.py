from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, EmailStr


class UserBaseSchema(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(UserBaseSchema):
    password: str

    @field_validator('password')
    def password_validator(cls, value):
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters')

        return value


class UserReadSchema(UserBaseSchema):
    is_active: bool
    created_at: datetime


class UserInDBSchema(UserReadSchema):
    hashed_password: str


class UserResponseSchema(UserBaseSchema):
    pass
