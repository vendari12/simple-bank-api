from fastapi import APIRouter, Depends, Security
from server.controllers.transactions import (fetch_transaction_by_code,
                                             initiate_transaction,
                                             list_account_transactions)
from server.schemas.transactions import (CreateTransactionSchema,
                                         FilterTransactionSchema,
                                         PaginatedTransactionSchema,
                                         RequestTransactionSchema,
                                         TransactionSchema)
from server.utils.db import get_session
from server.utils.jwt import JwtAuthorizationCredentials, access_security
from sqlalchemy.ext.asyncio import AsyncSession

transactions = APIRouter()


@transactions.get("/", response_model=PaginatedTransactionSchema)
async def fetch_transactions(
    filters: FilterTransactionSchema = Depends(),
    credentials: JwtAuthorizationCredentials = Security(access_security),
    session: AsyncSession = Depends(get_session),
):
    return await list_account_transactions(filters, credentials["id"], session)


@transactions.post("/", response_model=TransactionSchema)
async def create_transaction(
    payload: RequestTransactionSchema,
    credentials: JwtAuthorizationCredentials = Security(access_security),
    session: AsyncSession = Depends(get_session),
):
    return await initiate_transaction(payload, credentials["id"], session)


@transactions.get(
    "/{account_number}/{tranaction_code}", response_model=PaginatedTransactionSchema
)
async def get_transaction(
    transaction_code: str,
    account_number: str,
    credentials: JwtAuthorizationCredentials = Security(access_security),
    session: AsyncSession = Depends(get_session),
):
    return await fetch_transaction_by_code(
        transaction_code, credentials["id"], account_number, session
    )