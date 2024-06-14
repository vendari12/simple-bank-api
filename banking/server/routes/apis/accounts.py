from http import HTTPStatus

from fastapi import APIRouter, Depends, Security
from server.controllers.accounts import (create_user_account,
                                         fetch_user_account_details_by_number,
                                         get_user_accounts)
from server.schemas.accounts import (ListUserAccountSchema, OpenAccountSchema,
                                     QueryAccountFilter, UserAccountSchema)
from server.utils.db import AsyncSession, get_session
from server.utils.jwt import JwtAuthorizationCredentials, access_security

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
