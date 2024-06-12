from http import HTTPStatus

from fastapi import APIRouter, Depends
from fastapi_jwt import JwtAccessBearer, JwtAuthorizationCredentials
from server.config.settings import get_settings
from server.controllers.user import (authenticate_user, create_user,
                                     map_user_auth_claims)
from server.schemas.user import (CreateUserSchema, LoginUserResponseSchema,
                                 LoginUserSchema, PasswordResetSchema)
from server.utils.db import AsyncSession, get_session

user = APIRouter()
access_security = JwtAccessBearer(secret_key=get_settings().SECRET_KEY, auto_error=True)


@user.post("/auth", response_model=LoginUserResponseSchema, status_code=HTTPStatus.CREATED)
async def login(payload:LoginUserSchema, session:AsyncSession = Depends(get_session)):
    user = await authenticate_user(payload, session)
    return map_user_auth_claims(user, access_security)

@user.post("/", response_model=LoginUserResponseSchema, status_code=HTTPStatus.CREATED)
async def registration(payload: CreateUserSchema, session: AsyncSession = Depends(get_session)):
    user = await create_user(payload, session)
    return map_user_auth_claims(user, access_security)