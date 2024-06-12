import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

import pyotp
from passlib.hash import bcrypt
from server.config.settings import get_settings
from server.utils.constants import DEFAULT_CASCADE_MODE
from server.utils.db import BaseModel
from sqlalchemy import Enum, ForeignKey, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import EmailType, PhoneNumberType

from .enums import TokenTypeEnum, UserRole


class UserToken(BaseModel):
    """
    Stores a user-issued token object.

    Attributes:
        userId (Mapped[str]): The user ID associated with this token.
        tokenType (Mapped[TokenTypeEnum]): The type of token (e.g., account confirmation, password reset).
        expiry (Mapped[int]): The expiry duration of the token in seconds.
        token (Mapped[int]): The actual token value.
    """

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tokenType: Mapped[TokenTypeEnum] = mapped_column(String(25), index=True)
    expiry: Mapped[int]  # in seconds
    token: Mapped[int]

    @classmethod
    async def get_valid_token(
        cls,
        session: AsyncSession,
        user_id: int,
        token: int,
        token_type: TokenTypeEnum,
        expiry_threshold: datetime,
    ) -> Optional["UserToken"]:
        """Fetches a valid token for a user that matches the provided token and token type and is not expired."""
        stmt = select(cls).where(
            cls.user_id == user_id,
            cls.token == token,
            cls.tokenType == token_type,
            cls.created_at + timedelta(seconds=cls.expiry) > expiry_threshold,
        )
        result = await session.execute(stmt)
        return result.scalars().first()


class ContactDetails(BaseModel):
    """Represents contact details for users or branches."""

    __tablename__ = "contact_details"

    email: Mapped[str] = mapped_column(EmailType, nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(PhoneNumberType(region="US"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False, index=True)
    user = relationship("User", back_populates="contact_details", uselist=False)
    branch = relationship("Branch", back_populates="contact_details", uselist=False)

    def __repr__(self) -> str:
        return f"<ContactDetails(email={self.email}, phone={self.phone})>"


class User(BaseModel):
    """Maps a user instance to the DB"""

    first_name: Mapped[str]
    last_name: Mapped[str]
    username: Mapped[str] = mapped_column(index=True, unique=True)
    password_hash: Mapped[str]
    date_of_birth: Mapped[str]
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER)
    contact_details_id: Mapped[int] = mapped_column(ForeignKey("contact_details.id"))
    tokens: List[UserToken] = relationship(
        "UserToken", lazy="dynamic", back_populates="user_id"
    )
    contact_details = relationship("ContactDetails", back_populates="user")
    employee: Mapped["Employee"] = relationship(back_populates="user")
    accounts = relationship(
        "Account", back_populates="user", cascade=DEFAULT_CASCADE_MODE
    )
    is_deactivated: Mapped[bool] = mapped_column(default=False, index=True)

    @property
    def full_name(self) -> str:
        """
        Returns the full name of the user.

        Returns:
            str: The user's full name in the format "firstName lastName".
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def password(self):
        """
        Prevents reading of the password directly.

        Raises:
            AttributeError: Always raises an error as the password is not readable.
        """
        raise AttributeError("`password` is not a readable attribute")

    @password.setter
    def password(self, password: str):
        """
        Sets the user's password by hashing it.

        Args:
            password (str): The plain-text password to hash and set.
        """
        self.password_hash = bcrypt.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        """
        Verifies if the provided password matches the stored hash.

        Args:
            plain_password (str): The plain-text password to verify.

        Returns:
            bool: True if the password matches the stored hash, False otherwise.
        """
        return bcrypt.verify(plain_password, self.password_hash)

    async def generate_confirmation_token(
        self, session: AsyncSession, expiration=10800
    ) -> str:
        """
        Generates a confirmation token for account verification.

        Args:
            session (AsyncSession): The database session.
            expiration (int): The token's expiry time in seconds (default is 3 hours).

        Returns:
            str: The generated token.
        """
        return await self.generate_otp(
            expiration, TokenTypeEnum.ACCOUNT_CONFIRM.value, session
        )

    async def generate_email_change_token(
        self, session: AsyncSession, expiration=10800
    ) -> str:
        """
        Generates a token to verify email change requests.

        Args:
            session (AsyncSession): The database session.
            expiration (int): The token's expiry time in seconds (default is 3 hours).

        Returns:
            str: The generated token.
        """
        return await self.generate_otp(
            expiration, TokenTypeEnum.EMAIL_CHANGE.value, session
        )

    async def generate_password_reset_token(
        self, session: AsyncSession, expiration=10800
    ) -> str:
        """
        Generates a token to reset the user's password.

        Args:
            session (AsyncSession): The database session.
            expiration (int): The token's expiry time in seconds (default is 3 hours).

        Returns:
            str: The generated token.
        """
        return await self.generate_otp(
            expiration, TokenTypeEnum.PASSWORD_RESET.value, session
        )

    async def generate_otp(
        self, expiration: int, token_type: TokenTypeEnum, session: AsyncSession
    ) -> str:
        """
        Generates a one-time password (OTP) token for the user.

        Args:
            expiration (int): The token's expiry time in seconds.
            token_type (TokenTypeEnum): The type of token being generated.
            session (AsyncSession): The database session.

        Returns:
            str: The generated OTP token.
        """
        settings = get_settings()
        handler = pyotp.TOTP(settings.SECRET_KEY)
        token = handler.now()
        await UserToken.create(
            session,
            **{
                "user_id": self.id,
                "token": int(token),
                "expiry": expiration,
                "tokenType": token_type,
            },
        )
        return token

    async def verify_user_token(
        self,
        token: int,
        token_type: TokenTypeEnum,
        session: AsyncSession,
        expiration=10800,
    ) -> bool:
        """
        Verifies if the provided token matches a token issued for the user.

        Args:
            token (int): The token to verify.
            token_type (TokenTypeEnum): The type of token to verify against.
            session (AsyncSession): The database session.
            expiration (int): The token's expiry time in seconds (default is 3 hours).

        Returns:
            bool: True if the token is valid and not expired, False otherwise.
        """
        try:
            # Current UTC time
            now = datetime.now(datetime.UTC)

            # Calculate the expiration threshold
            expiration_threshold = now - timedelta(seconds=expiration)

            # Fetch the valid token directly from the database
            user_token = await UserToken.get_valid_token(
                session,
                user_id=self.id,
                token=token,
                token_type=token_type,
                expiry_threshold=expiration_threshold,
            )

            # Check if the token is found and not expired
            if user_token:
                return True

        except Exception as e:
            logging.error(f"Error verifying token for user {self.id}: {e}")

        return False

    @property
    def age(self) -> Optional[int]:
        """
        Calculates the user's age from their date of birth (DOB).

        Returns:
            Optional[int]: The user's age if Ddate of birth is valid, otherwise None.
        """
        try:
            dob_year, dob_month, dob_day = map(int, self.date_of_birth.split("-"))
            user_birth_date = date(dob_year, dob_month, dob_day)
            today = date.today()
            return (
                today.year
                - user_birth_date.year
                - (
                    (today.month, today.day)
                    < (user_birth_date.month, user_birth_date.day)
                )
            )
        except Exception as ex:
            logging.error(
                f"Failed to compute user: {self.full_name} age from date of birth: {ex}"
            )
            return None

    @staticmethod
    async def load_default_users(session: AsyncSession):
        """
        Generates a number of fake users for testing purposes.

        Args:
            session (AsyncSession): The database session.
            count (int): The number of fake users to generate (default is 1000).
            **kwargs: Additional keyword arguments to customize user attributes.
        """
        from server.utils.files import BASE_PATH, load_template
        from sqlalchemy.exc import IntegrityError

        default_password = "Password"
        users = load_template(f"{BASE_PATH}/default_users.json")
        try:
            users_instances = [
                User(
                    firstName=user["name"].split(" ")[0],
                    lastName=user["name"].split(" ")[1],
                    email=user["email"],
                    country=user["country"],
                    state=user["state"],
                    password=default_password,
                    username=user["name"],
                )
                for user in users["users"]
            ]
            session.add_all(users_instances)
            await session.commit()
            logging.info(f"Added {len(users_instances)} default users")
        except IntegrityError as e:
            logging.error(f"Could'nt save default users due to: {e.detail}")


class Employee(BaseModel):
    """Represents an employee of the bank."""

    __tablename__ = "employees"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="employee")
    branch = relationship("Branch", back_populates="employees")

    def __repr__(self) -> str:
        return f"<Employee(name={self.name}, position={self.position})>"
