from datetime import datetime
from typing import Optional

from pycountry import countries
from pydantic import (BaseModel, ConfigDict, EmailStr, Field, SecretStr,
                      field_validator)
from server.utils.schema import BaseSchema

_INVALID_COUNTRY_ERROR_MESSAGE = ""


class LoginUserSchema(BaseSchema):
    username: str
    password: SecretStr


class LoginUserResponseSchema(BaseSchema):
    access_token: str
    refresh_token: str


class CreateUserSchema(BaseSchema):
    first_name: str = Field(..., description="The first name of the user.")
    last_name: str = Field(..., description="The last name of the user.")
    password: SecretStr = Field(..., description="The password.")
    username: str = Field(..., description="A user's preferred username.")
    date_of_birth: str = Field(
        ..., description="The user's date of birth in YYYY-MM-DD format."
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value):
        """Validates the user's date of birth to ensure it adheres to the format (YYYY-MM-DD).

        Args:
            value (str): The date of birth field.

        Raises:
            ValueError: If the date of birth format is invalid.

        Returns:
            str: The validated date of birth string.
        """
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date of birth must be in the format YYYY-MM-DD")
        return value


class ForgotPasswordSchema(BaseSchema):
    email: EmailStr


class PasswordResetSchema(BaseSchema):
    token: str
    newPassword: SecretStr
    email: EmailStr


class UpdateUserDetailsSchema(BaseSchema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value):
        """Validates the user's date of birth to ensure it adheres to the format (YYYY-MM-DD).

        Args:
            value (str): The date of birth field.

        Raises:
            ValueError: If the date of birth format is invalid.

        Returns:
            str: The validated date of birth string.
        """
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date of birth must be in the format YYYY-MM-DD")
        return value


class BaseContactDetailsSchema(BaseSchema):
    country: str

    @field_validator("country")
    @classmethod
    def validate_countries(cls, field):
        if isinstance(field, str):
            try:
                country = countries.search_fuzzy(field)
                if not country:
                    raise ValueError(_INVALID_COUNTRY_ERROR_MESSAGE)
            except LookupError:
                raise ValueError(_INVALID_COUNTRY_ERROR_MESSAGE)
        return field


class UpdateUserContactDetailSchema(BaseContactDetailsSchema):
    country: Optional[str] = None
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    is_primary: Optional[bool] = None
    address: Optional[str] = None


class CreateUserContactDetailSchema(BaseContactDetailsSchema):
    email: str
    city: str
    state: str
    zip_code: str
    is_primary: bool
    address: str


class UserContactDetailsSchema(CreateUserContactDetailSchema):
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class UserSchema(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    contacts: UserContactDetailsSchema
    id: int
    model_config = ConfigDict(from_attributes=True)
