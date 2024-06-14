from datetime import timedelta
from typing import List, Optional

from fastapi_jwt import JwtAccessBearer
from pydantic import EmailStr
from server.config.settings import get_settings
from server.models.user import ContactDetails, User, UserRole, UserToken
from server.schemas.user import (CreateUserContactDetailSchema,
                                 CreateUserSchema, LoginUserResponseSchema,
                                 LoginUserSchema,
                                 UpdateUserContactDetailSchema,
                                 UpdateUserDetailsSchema,
                                 UserContactDetailsSchema, UserSchema)
from server.utils.exceptions import (BadRequest, DuplicatedEntryError,
                                     ObjectNotFound)
from sqlalchemy.ext.asyncio import AsyncSession

_USER_NOT_FOUND_ERROR_MESSAGE = "User doesn't exist"


def map_user_auth_claims(
    user: User, handler: JwtAccessBearer
) -> LoginUserResponseSchema:
    settings = get_settings()
    claims = {"username": user.username, "id": user.id}
    return LoginUserResponseSchema(
        access_token=handler.create_access_token(
            subject=claims, expires_delta=timedelta(settings.ACCESS_TOKEN_EXPIRY)
        ),
        refresh_token=handler.create_refresh_token(
            claims, expires_delta=timedelta(settings.REFRESH_TOKEN_EXPRY)
        ),
    )


async def _get_user_by_username(username: str, session: AsyncSession) -> User:
    user = await User.get_by_field(username, "username", session)
    if not user:
        raise ObjectNotFound(_USER_NOT_FOUND_ERROR_MESSAGE)
    return user


async def _get_user_by_id(id: int, session: AsyncSession) -> User:
    """Retrieves a user by their identifier (id)

    Args:
        id (int):
        session (AsyncSession):

    Raises:
        ObjectNotFound: If user not found

    Returns:
        User:
    """
    user = await User.get_by_field(id, "id", session)
    if user:
        return user
    raise ObjectNotFound(_USER_NOT_FOUND_ERROR_MESSAGE)


async def create_user(payload: CreateUserSchema, session: AsyncSession) -> User:
    """Creates a new user instance

    Args:
        payload (CreateUserSchema): Request payload for user detail
        session (AsyncSession):

    Raises:
        DuplicatedEntryError: If a user already exists

    Returns:
        User:
    """
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
    """Performs a basic password authentication for a user

    Args:
        payload (LoginUserSchema): Basic auth payload
        session (AsyncSession):

    Raises:
        BadRequest: If details are not valid

    Returns:
        User: Authenticated User
    """
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


async def _get_user_contact_by_id(
    user: int, contact_id: int, session: AsyncSession
) -> ContactDetails:
    """Returns a user contact by it Id

    Args:
        user (int):
        contact_id (int):
        session (AsyncSession):

    Raises:
        ObjectNotFound: If object not found

    Returns:
        ContactDetails:
    """
    contact = await ContactDetails.get_one_by_multiple(
        session, **{"user_id": user, "id": contact_id}
    )
    if contact:
        return contact
    raise ObjectNotFound("Requested contact details not found")


async def create_user_contact(
    user: int, payload: CreateUserContactDetailSchema, session: AsyncSession
) -> UserContactDetailsSchema:
    """Create a contact record for a user

    Args:
        user (int): User identifier
        payload (CreateUserContactDetailSchema): Contact details
        session (AsyncSession):

    raises:
        DuplicatedEntryError: If a contact with same (unique) values exist

    Returns:
        UserContactDetailsSchema: Created contact details
    """
    user = await _get_user_by_id(user, session)
    contact = await ContactDetails.create(session, **payload.model_dump())
    return UserContactDetailsSchema.model_validate(contact)


async def update_user_contact_details(
    user: int,
    contact_id: int,
    payload: UpdateUserContactDetailSchema,
    session: AsyncSession,
) -> UserContactDetailsSchema:
    """Updates a user contact record

    Args:
        user (int):
        contact_id (int): Contact identifier
        payload (UpdateUserContactDetailSchema): Records to update
        session (AsyncSession):

    Returns:
        UserContactDetailsSchema: Updated contact details
    """
    contact = await _get_user_contact_by_id(user, contact_id, session)
    updated_contact = await contact.update(
        session, payload.model_dump(exclude_unset=True, exclude_none=True)
    )
    return UserContactDetailsSchema.model_validate(updated_contact)
