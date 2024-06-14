from decimal import Decimal
from unittest.mock import AsyncMock, patch, Mock
from server.utils.constants import USER_MAX_ACCOUNT_LIMIT
import pytest
from server.controllers.accounts import (
    _get_user_account_by_number,
    _list_user_accounts,
    create_user_account,
    fetch_user_account_details_by_number,
    get_user_accounts,
)
from server.models.accounts import Account, SIGNUP_ACCOUNT_TOPUP
from server.models.enums import AccountLevel, AccountStatus, AccountType
from server.utils.db import BaseModel
from server.schemas.accounts import (
    ListUserAccountSchema,
    OpenAccountSchema,
    QueryAccountFilter,
    UserAccountSchema,
)
from server.utils.exceptions import BadRequest, ObjectNotFound
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_user_account_by_number_success(
    db_session, sample_account, test_user
):
    result = await _get_user_account_by_number(
        sample_account.number, test_user.id, db_session
    )
    assert result == sample_account


@pytest.mark.asyncio
async def test_get_user_account_by_number_not_found(db_session, test_user):

    with pytest.raises(
        ObjectNotFound, match="No account with number: 123456 found for this user"
    ):
        await _get_user_account_by_number("123456", test_user.id, db_session)


@pytest.mark.asyncio
async def test_list_user_accounts_success(db_session, test_user, sample_account):
    result = await _list_user_accounts(test_user.id, db_session)
    assert len(result) == 1
    assert result[0] == sample_account


@pytest.mark.asyncio
async def test_list_user_accounts_empty(db_session, test_user):
    result = await _list_user_accounts(test_user.id, db_session)
    assert result == []


@pytest.mark.parametrize(
    "status,type,level,expected",
    [
        (AccountStatus.ACTIVE, AccountType.CHECKINGS, AccountLevel.BASIC, 1),
        (AccountStatus.CLOSED, AccountType.CHECKINGS, AccountLevel.BASIC, 0),
    ],
)
@pytest.mark.asyncio
async def test_get_user_accounts_with_filter_success(
    db_session, test_user, sample_account, status, type, level, expected
):
    filters = QueryAccountFilter(status=status, level=level, type=type)

    result = await get_user_accounts(test_user.id, filters, db_session)

    assert len(result.accounts) == expected
    assert isinstance(result, ListUserAccountSchema)


@pytest.mark.asyncio
async def test_create_user_account_success(
    mocker,
    db_session,
    test_user,
):
    payload = OpenAccountSchema(
        type=AccountType.CHECKINGS, currency="USD", level=AccountLevel.BASIC
    )
    result = await create_user_account(test_user.id, payload, db_session)
    assert result.number != None
    assert isinstance(result, UserAccountSchema)
    assert result.balance == SIGNUP_ACCOUNT_TOPUP and result.currency == "USD"
    assert result.type == AccountType.CHECKINGS and result.level == AccountLevel.BASIC


@pytest.mark.asyncio
async def test_create_user_account_exceed_limit(mocker, test_user, db_session):
    mock_get_all_by_multiple = mocker.patch.object(BaseModel, "get_all_by_multiple")
    mock_get_all_by_multiple.return_value = [
        Mock()
    ] * USER_MAX_ACCOUNT_LIMIT  # Mock user having max accounts

    payload = OpenAccountSchema(
        type=AccountType.CHECKINGS, currency="USD", level=AccountLevel.BASIC
    )

    with pytest.raises(
        BadRequest,
        match="You have exceeded the maximum number of accounts you can create",
    ):
        await create_user_account(test_user.id, payload, db_session)


@pytest.mark.asyncio
async def test_fetch_account_details_by_number_success(
    db_session, sample_account, test_user
):
    result = await fetch_user_account_details_by_number(
        sample_account.number, test_user.id, db_session
    )
    assert result.number == sample_account.number
    assert isinstance(result, UserAccountSchema)
