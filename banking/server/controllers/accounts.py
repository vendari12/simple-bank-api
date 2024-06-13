import logging
from typing import Dict, List, Optional

from server.models.accounts import Account
from server.schemas.accounts import (
    ListUserAccountSchema,
    OpenAccountSchema,
    QueryAccountFilter,
    UserAccountSchema,
)
from server.utils.accounts import generate_user_account_number
from server.utils.constants import USER_MAX_ACCOUNT_LIMIT
from server.utils.exceptions import BadRequest, ObjectNotFound
from sqlalchemy.ext.asyncio import AsyncSession


async def _get_user_account_by_number(
    number: str, user: int, session: AsyncSession
) -> Account:
    """
    Retrieves a user's bank account by its number.

    Args:
        number (str): Bank account number (unique identifier).
        user (int): User ID (account owner).
        session (AsyncSession): Database session.

    Raises:
        ObjectNotFound: If no account matches the provided number for the user.

    Returns:
        Account: The user's account matching the provided number.
    """
    logging.debug(f"Fetching account for user {user} by number {number}")

    account = await Account.get_one_by_multiple(
        session, **{"number": number, "user_id": user}
    )

    if not account:
        logging.error(f"Account with number {number} not found for user {user}")
        raise ObjectNotFound(f"No account with number: {number} found for this user")

    logging.info(f"Account with number {number} retrieved for user {user}")
    return account


async def _list_user_accounts(
    user: int, session: AsyncSession, query: Optional[Dict] = None
) -> List[Account]:
    """
    Retrieves a list of accounts owned by a user, with optional filtering.

    Args:
        user (int): User ID (account owner).
        session (AsyncSession): Database session.
        query (Optional[Dict], optional): Additional filter query. Defaults to None.

    Returns:
        List[Account]: A list of accounts owned by the user.
    """
    query = query or {}
    query["user_id"] = user
    logging.debug(f"Listing accounts for user {user} with query: {query}")

    accounts = await Account.get_all_by_multiple(session, **query)

    logging.info(f"Retrieved {len(accounts)} accounts for user {user}")
    return accounts


async def get_user_accounts(
    user: int, filters: QueryAccountFilter, session: AsyncSession
) -> ListUserAccountSchema:
    """
    Retrieves a list of the user's bank accounts, applying any provided filters.

    Args:
        user (int): User ID (account owner).
        filters (QueryAccountFilter): Filters to apply to the query.
        session (AsyncSession): Database session.

    Returns:
        ListUserAccountSchema: A schema containing the user's bank accounts.
    """
    query = filters.model_dump(exclude_none=True, exclude_unset=True)
    logging.debug(f"Fetching accounts for user {user} with filters: {query}")

    accounts = await _list_user_accounts(user, session, query)

    account_schemas = [
        UserAccountSchema.model_validate(account) for account in accounts
    ]
    logging.info(f"Accounts fetched for user {user}: {account_schemas}")

    return ListUserAccountSchema(accounts=account_schemas, user_id=user)


async def create_user_account(
    user: int, payload: OpenAccountSchema, session: AsyncSession
) -> UserAccountSchema:
    """
    Creates a bank account for a user.

    Args:
        user (int): User ID (account owner).
        payload (OpenAccountSchema): Details for the new account.
        session (AsyncSession): Database session.

    Raises:
        BadRequest: If the user has exceeded the maximum number of accounts allowed.

    Returns:
        UserAccountSchema: Schema of the newly created account.
    """
    logging.debug(f"Creating account for user {user} with payload: {payload}")

    user_accounts = await _list_user_accounts(user, session)

    if len(user_accounts) >= USER_MAX_ACCOUNT_LIMIT:
        logging.error(
            f"User {user} exceeded max account limit of {USER_MAX_ACCOUNT_LIMIT}"
        )
        raise BadRequest(
            "You have exceeded the maximum number of accounts you can create"
        )

    account_number = generate_user_account_number()
    data = {**payload.model_dump(), "number": account_number, "user_id": user}
    account = await Account.create(session, **data)

    logging.info(f"Account created for user {user} with number {account_number}")
    return UserAccountSchema.model_validate(account)


async def fetch_account_details_by_number(
    number: str, user: int, session: AsyncSession
) -> UserAccountSchema:
    """
    Retrieves a user's account details by the account number.

    Args:
        number (str): Account number (unique identifier).
        user (int): User ID (account owner).
        session (AsyncSession): Database session.

    Raises:
        ObjectNotFound: If no account matches the provided number for the user.

    Returns:
        UserAccountSchema: Schema containing the account details.
    """
    logging.debug(
        f"Fetching account details for user {user} with account number {number}"
    )

    account = await _get_user_account_by_number(number, user, session)

    account_schema = UserAccountSchema.model_validate(account)
    logging.info(
        f"Account details retrieved for user {user} with account number {number}"
    )

    return account_schema
