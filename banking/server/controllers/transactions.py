import logging
from typing import Dict, List, Optional

from server.config.settings import settings
from server.models.accounts import Account, Transaction, TransactionType
from server.schemas.transactions import (
    CreateTransactionSchema,
    PaginatedTransactionSchema,
    TransactionSchema,
    FilterTransactionSchema,
)
from server.utils.cache import RedisLock, construct_resource_lock_key, get_redis_client
from server.utils.db import Page
from server.utils.exceptions import BadRequest, ObjectNotFound
from server.utils.strategies import TransactionFactory
from server.utils.transactions import generate_transaction_code
from sqlalchemy.ext.asyncio import AsyncSession

from .accounts import _get_user_account_by_number, fetch_account_details_by_number

logger = logging.getLogger(__name__)


async def process_account_transaction(
    payload: CreateTransactionSchema, session: AsyncSession
) -> TransactionSchema:
    """
    Processes a transaction based on the provided payload.

    Args:
        payload (CreateTransactionSchema): Data for creating the transaction.
        session (AsyncSession): The database session.

    Returns:
        TransactionSchema: The created transaction details.
    """
    logger.debug(f"Processing transaction with payload: {payload}")

    handler = TransactionFactory.create(payload.type)
    transaction = await handler.execute(payload, session)

    logger.info(f"Transaction processed with code: {transaction.code}")

    return TransactionSchema.model_validate(transaction)


async def _get_transaction_by_code(
    account_id: int, code: str, session: AsyncSession
) -> Transaction:
    """
    Retrieves a transaction by its code for a specific account.

    Args:
        account_id (int): The ID of the account.
        code (str): The transaction reference code.
        session (AsyncSession): The database session.

    Raises:
        ObjectNotFound: If the transaction with the specified code is not found.

    Returns:
        Transaction: The found transaction.
    """
    logger.debug(f"Fetching transaction for account_id: {account_id}, code: {code}")

    transaction = await Transaction.get_one_by_multiple(
        session, **{"account_id": account_id, "code": code}
    )
    if not transaction:
        logger.error(f"Transaction with code {code} not found for account {account_id}")
        raise ObjectNotFound(f"Transaction with reference code '{code}' not found.")

    logger.info(f"Transaction with code {code} retrieved for account {account_id}")

    return transaction


async def fetch_transaction_by_code(
    code: str, user: int, account_number: str, session: AsyncSession
) -> TransactionSchema:
    """
    Retrieves a transaction by its code for a user's account.

    Args:
        code (str): The transaction reference code.
        user (int): The user ID.
        account_number (str): The user's account number.
        session (AsyncSession): The database session.

    Returns:
        TransactionSchema: The transaction details.
    """
    logger.debug(
        f"Fetching transaction by code: {code} for user: {user} and account: {account_number}"
    )

    account = await _get_user_account_by_number(account_number, user, session)
    transaction = await _get_transaction_by_code(account.id, code, session)

    logger.info(f"Transaction with code {code} retrieved for user {user}")

    return TransactionSchema.model_validate(transaction)


async def _list_account_transactions(
    filters: FilterTransactionSchema,
    user: int,
    session: AsyncSession,
) -> Page:
    """
    Lists transactions for an account with optional filtering and pagination.

    Args:
        user (int): The user ID.
        session (AsyncSession): The database session.
        filters (FilterTransactionSchema): filters for transactions.

    Returns:
        Page: A page of transactions.
    """
    logger.debug(
        f"Listing transactions for account_number: {filters.account_number}, user: {user}, page: {filters.page}"
    )

    account = await fetch_account_details_by_number(
        filters.account_number, user, session
    )
    filters_dict = filters.model_dump(
        exclude_unset=True,
        exclude_none=True,
        exclude=("page", "per_page", "account_number"),
    )
    transactions = await Transaction.paginate(
        filters.page,
        session,
        filters.per_page,
        **{**filters_dict, "account_id": account.id},
    )

    logger.info(
        f"Retrieved {len(transactions.items)} transactions for account {filters.account_number}"
    )

    return transactions


async def list_account_transactions(
    filters: FilterTransactionSchema,
    user: int,
    session: AsyncSession,
) -> PaginatedTransactionSchema:
    """
    Retrieves a paginated list of transactions for a specific account.

    Args:
        user (int): The user ID.
        session (AsyncSession): The database session.
        filters (Optional[Dict], optional): Additional filters for transactions..

    Returns:
        PaginatedTransactionSchema: A paginated schema of transactions.
    """

    transactions = await _list_account_transactions(filters, user, session)

    paginated_transactions = PaginatedTransactionSchema(
        transactions=[
            TransactionSchema.model_validate(transaction)
            for transaction in transactions.items
        ],
        page=transactions.page,
        per_page=transactions.page_size,
        next_page=transactions.next_page,
        previous_page=transactions.prev_page,
    )

    logger.info(f"Page {paginated_transactions.page} of transactions retrieved for account {filters.account_number}")

    return paginated_transactions
