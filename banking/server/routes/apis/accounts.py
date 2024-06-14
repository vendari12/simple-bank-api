from http import HTTPStatus
from fastapi import APIRouter, Depends, Security
from server.schemas.accounts import (
    OpenAccountSchema,
    UserAccountSchema,
    ListUserAccountSchema,
    QueryAccountFilter,
)
from server.controllers.accounts import (
    get_user_accounts,
    fetch_user_account_details_by_number,
    create_user_account,
)
from server.utils.jwt import access_security, JwtAuthorizationCredentials
from server.utils.db import get_session, AsyncSession

accounts = APIRouter()


@accounts.post("/", response_model=UserAccountSchema, status_code=HTTPStatus.CREATED)
async def open_account(
    payload: OpenAccountSchema,
    session: AsyncSession = Depends(get_session),
    credential: JwtAuthorizationCredentials = Security(access_security),
):
    return await create_user_account(credential["id"], payload, session)


@accounts.get("/{account_number}/", response_model=UserAccountSchema)
async def get_account(
    account_number: str,
    session: AsyncSession = Depends(get_session),
    credential: JwtAuthorizationCredentials = Security(access_security),
):
    return await fetch_user_account_details_by_number(
        account_number, credential["id"], session
    )


@accounts.get("/", response_model=ListUserAccountSchema)
async def list_user_accounts(
    filters: QueryAccountFilter = Depends(),
    session: AsyncSession = Depends(get_session),
    credential: JwtAuthorizationCredentials = Security(access_security),
):
    return await get_user_accounts(credential["id"], filters, session)
