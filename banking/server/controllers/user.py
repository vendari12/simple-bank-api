from datetime import timedelta
from typing import List, Optional

from fastapi_jwt import JwtAccessBearer
from pydantic import EmailStr
from server.config.settings import get_settings
from server.models.user import User, UserRole, UserToken
from server.schemas.user import (CreateUserSchema, LoginUserResponseSchema,
                                 LoginUserSchema, UpdateUserDetailsSchema,
                                 UserSchema)
from server.utils.exceptions import (BadRequest, DuplicatedEntryError,
                                     ObjectNotFound)
from sqlalchemy.ext.asyncio import AsyncSession

_USER_NOT_FOUND_ERROR_MESSAGE = "User doesn't exist"


def map_user_auth_claims(
    user: User, handler: JwtAccessBearer
) -> LoginUserResponseSchema:
    settings = get_settings()
    claims = {"sub": user.username}
    return LoginUserResponseSchema(
        access_token=handler.create_access_token(
            subject=claims, expires_delta=timedelta(settings.ACCESS_TOKEN_EXPIRY)
        ),
        access_token=handler.create_refresh_token(
            claims, expires_delta=timedelta(settings.REFRESH_TOKEN_EXPRY)
        ),
    )


async def _get_user_by_username(username: str, session: AsyncSession) -> User:
    user = await User.get_by_field(username, "username", session)
    if not user:
        raise ObjectNotFound(_USER_NOT_FOUND_ERROR_MESSAGE)
    return user


async def _get_user_by_id(id: int, session: AsyncSession) -> User:
    user = await User.get_by_field(id, "id", session)
    if user:
        return user
    raise ObjectNotFound(_USER_NOT_FOUND_ERROR_MESSAGE)


async def create_user(payload: CreateUserSchema, session: AsyncSession) -> User:
    payload_dict = payload.model_dump()
    payload_dict.update({"password": payload.password.get_secret_value()})
    user_in_db = await User.get_by_field(payload.username, "username", session)
    if not user_in_db:
        user = await User.create(session, **payload_dict)
        return user
    raise DuplicatedEntryError(
        f"User with username: {user_in_db.username} already exists"
    )


async def authenticate_user(payload: LoginUserSchema, session: AsyncSession) -> User:
    user_in_db = await User.get_by_field(payload.username, "username", session)
    if user_in_db and user_in_db.verify_password(payload.password.get_secret_value()):
        return user_in_db
    raise BadRequest("Invalid username or password")


async def get_user_details(username: str, session: AsyncSession) -> UserSchema:
    """Fetches a user deta

    Args:
        username (str): Target user's username
        session (AsyncSession): DB session

    Returns:
        UserSchema: users details
    """
    user = await _get_user_by_username(username, session)
    return UserSchema.model_validate(user)
