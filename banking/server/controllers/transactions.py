import logging
from datetime import datetime
from typing import Dict, List, Optional

from server.config.settings import settings
from server.models.accounts import Account, Transaction, TransactionType
from server.schemas.transactions import (
    CreateTransactionSchema,
    FilterTransactionSchema,
    PaginatedTransactionSchema,
    RequestTransactionSchema,
    TransactionSchema,
)
from server.utils.db import Page
from server.utils.exceptions import BadRequest, ObjectNotFound
from server.utils.queues import enqueue_task
from server.utils.strategies import TransactionFactory
from server.utils.transactions import generate_transaction_code
from sqlalchemy.ext.asyncio import AsyncSession

from .accounts import (
    _get_user_account_by_number,
    _get_account_by_number,
)

logger = logging.getLogger(__name__)

# naive way to handle this
# in a more roboust way this data should be fetched from a processing house/API if external
# and would ideally contain more information than this
_BANK_NAME = "Some Bank"


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

    account = await _get_user_account_by_number(filters.account_number, user, session)
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

    logger.info(
        f"Page {paginated_transactions.page} of transactions retrieved for account {filters.account_number}"
    )

    return paginated_transactions


async def _create_transaction(
    payload: CreateTransactionSchema, session: AsyncSession
) -> Transaction:
    code = generate_transaction_code(
        str(payload.account_id), payload.currency, datetime.now().isoformat()
    )
    transaction = await Transaction.create(
        session, **{**payload.model_dump(), "code": code}
    )
    return transaction


async def process_transaction_in_background(
    transaction: Transaction,
    account: Account,
    metadata: Dict,
    session: AsyncSession,
):
    """Processes a transaction in the background."""
    strategy = TransactionFactory.create(transaction.type)
    await strategy.execute(transaction, account, metadata, session)


def schedule_transaction(
    transaction: Transaction, account: Account, metadata: Dict, session: AsyncSession
):
    """Schedules the transaction to be processed asynchronously."""
    task = lambda: process_transaction_in_background(
        transaction, account, metadata, session
    )
    enqueue_task(task)


async def initiate_transaction(
    payload: RequestTransactionSchema, user: int, session: AsyncSession
) -> TransactionSchema:
    source = await _get_user_account_by_number(
        payload.source_account_number, user, session
    )
    destination_account = None
    if payload.destination_account_number:
        destination_account = await _get_account_by_number(
            payload.destination_account_number, session
        )
    metadata = {
        "sender": payload.source_account_number,
        "target_account_number": (
            destination_account.number if destination_account else destination_account
        ),
        "bank": _BANK_NAME,
        "tax": payload.tax
    }
    transaction_payload = CreateTransactionSchema(
        amount=payload.amount + payload.tax,
        account_id=source.id,
        description=f"{payload.type} for account {source.number}  {payload.destination_account_number if payload.destination_account_number else 'for CASH'}",
        type=payload.type,
        currency=payload.currency,
        extra=metadata,
    )
    transaction = await _create_transaction(transaction_payload, session)
    # send to queue for processing
    # ideally we would need to create a new session instance for sqlalchemy
    # for thread safety use
    schedule_transaction(transaction, source, metadata, session)
    return TransactionSchema.model_validate(transaction)
