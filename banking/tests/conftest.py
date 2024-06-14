import asyncio
from decimal import Decimal
from typing import Generator

import pytest
import pytest_asyncio
from fastapi_jwt import JwtAuthorizationCredentials
from fastapi_jwt.jwt import JwtAccess, JwtAuthorizationCredentials
from httpx import AsyncClient
from manage import app
from server.models.accounts import (Account, Transaction, TransactionStatus,
                                    TransactionType)
from server.models.enums import UserRole
from server.models.user import ContactDetails, User
from server.utils.constants import SERVICE_PORT
from server.utils.db import AsyncSession, Base, engine, url
from server.utils.exceptions import BadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from tests.fixtures.account import generate_account_data
from tests.fixtures.transactions import generate_transaction
from tests.fixtures.user import SAMPLE_USER_CONTACT_DETAILS, SAMPLE_USER_DATA


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def event_loop(request) -> Generator:
    # making the event loop accessible in the session
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session() as s:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture()
async def client() -> AsyncClient:
    async with AsyncClient(app=app, base_url=f"http://localhost:{SERVICE_PORT}") as ac:
        yield ac


@pytest_asyncio.fixture()
async def test_user(db_session):
    user = await User.create(db_session, **SAMPLE_USER_DATA)
    yield user
    await user.delete(db_session)


@pytest_asyncio.fixture()
async def sample_user_contacts(db_session, test_user):

    contact = await ContactDetails.create(
        db_session, **{**SAMPLE_USER_CONTACT_DETAILS, "user_id": test_user.id}
    )
    yield contact
    await contact.delete(db_session)


@pytest_asyncio.fixture()
async def sample_account(db_session, test_user):
    account = await Account.create(
        db_session, **{**generate_account_data(), "user_id": test_user.id}
    )
    yield account
    await account.delete(db_session)


@pytest_asyncio.fixture()
async def sample_account_transaction(db_session, sample_account):
    transaction = await Account.create(
        db_session, **{**generate_transaction(), "account_id": sample_account.id}
    )
    yield transaction
    await transaction.delete(db_session)


@pytest.fixture()
def mock_get_current_user(mocker, test_user):
    client = mocker.patch.object(JwtAccess, "_get_credentials")
    client.return_value = JwtAuthorizationCredentials(
        subject={"id": test_user.id, "username": test_user.username}
    )
    return client
