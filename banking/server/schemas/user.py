from typing import Optional

from pycountry import countries
from pydantic import (BaseModel, ConfigDict, EmailStr, SecretStr,
                      field_validator)
from server.utils.schema import BaseSchema


class LoginUserSchema(BaseSchema):
    username: str
    password: SecretStr


class LoginUserResponseSchema(BaseSchema):
    access_token: str
    refresh_token: str


class CreateUserSchema(BaseSchema):
    first_name: str
    Last_name: str
    password: SecretStr
    username: str
    dateOfBirth: str
    state: str
    email: EmailStr

    @field_validator("country")
    @classmethod
    def validate_countries(cls, field):
        if isinstance(field, str):
            try:
                country = countries.search_fuzzy(field)
                if not country:
                    raise ValueError("Not a valid country")
            except LookupError:
                raise ValueError("Not a valid country")
        return field


class ForgotPasswordSchema(BaseSchema):
    email: EmailStr


class PasswordResetSchema(BaseSchema):
    token: str
    newPassword: SecretStr
    email: EmailStr


class UpdateUserDetailsSchema(BaseSchema):
    first_name: Optional[str] = None
    Last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    state: Optional[str] = None


class UserSchema(BaseModel):
    first_name: str
    Last_name: str
    date_of_birth: str
    country: str
    id: int
    model_config = ConfigDict(from_attributes=True)
