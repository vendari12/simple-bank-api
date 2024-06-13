from typing import Optional
from datetime import datetime
from pycountry import countries
from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr, Field, field_validator
from server.utils.schema import BaseSchema


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



class UserSchema(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    id: int
    model_config = ConfigDict(from_attributes=True)

    
class CreateUserContactDetail(BaseSchema):
    country: str
    email: str
    user_id: int
    city: str
    state: str
    zip_code: str
    is_primary: bool
    address: str

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
