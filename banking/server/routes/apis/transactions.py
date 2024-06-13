from fastapi import APIRouter, Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession
from server.utils.db import get_session
from server.schemas.transactions import (
    CreateTransactionSchema,
    TransactionSchema,
    PaginatedTransactionSchema,
    FilterTransactionSchema,
)
from server.controllers.transactions import (
    list_account_transactions,
    fetch_transaction_by_code,
    process_account_transaction,
)
from server.utils.jwt import access_security, JwtAuthorizationCredentials

transactions = APIRouter()


@transactions.get("/", response_model=PaginatedTransactionSchema)
async def fetch_transactions(
    filters: FilterTransactionSchema = Depends(),
    credentials: JwtAuthorizationCredentials = Security(access_security),
    session: AsyncSession = Depends(get_session),
):
    return await list_account_transactions(filters, credentials["id"], session)


@transactions.get("/{account_number}/{tranaction_code}", response_model=PaginatedTransactionSchema)
async def get_transaction(
    code: str,
    account_number: str,
    credentials: JwtAuthorizationCredentials = Security(access_security),
    session: AsyncSession = Depends(get_session),
):
    return await fetch_transaction_by_code(code,)