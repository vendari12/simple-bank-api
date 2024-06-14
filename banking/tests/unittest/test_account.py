from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from server.controllers.accounts import (  # Replace 'my_module' with the actual module name
    _get_user_account_by_number, _list_user_accounts, create_user_account,
    fetch_account_details_by_number, get_user_accounts)
from server.models.accounts import Account
from server.schemas.accounts import (ListUserAccountSchema, OpenAccountSchema,
                                     QueryAccountFilter, UserAccountSchema)
from server.utils.exceptions import BadRequest, ObjectNotFound
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_user_account_by_number_success(setup_data):
    session, account, _ = setup_data
    session.get_one_by_multiple.return_value = account

    result = await _get_user_account_by_number("123456", 1, session)
    
    assert result == account
    session.get_one_by_multiple.assert_awaited_once_with(session, **{"number": "123456", "user_id": 1})

@pytest.mark.asyncio
async def test_get_user_account_by_number_not_found(setup_data):
    session, _, _ = setup_data
    session.get_one_by_multiple.return_value = None

    with pytest.raises(ObjectNotFound, match="No account with number: 123456 found for this user"):
        await _get_user_account_by_number("123456", 1, session)

@pytest.mark.asyncio
async def test_list_user_accounts_success(setup_data):
    session, account, account_list = setup_data
    session.get_all_by_multiple.return_value = account_list

    result = await _list_user_accounts(1, session)
    
    assert result == account_list
    session.get_all_by_multiple.assert_awaited_once_with(session, user_id=1)

@pytest.mark.asyncio
async def test_list_user_accounts_empty(setup_data):
    session, _, _ = setup_data
    session.get_all_by_multiple.return_value = []

    result = await _list_user_accounts(1, session)
    
    assert result == []
    session.get_all_by_multiple.assert_awaited_once_with(session, user_id=1)

@pytest.mark.asyncio
async def test_get_user_accounts_success(setup_data):
    session, account, account_list = setup_data
    session.get_all_by_multiple.return_value = account_list
    filters = QueryAccountFilter()

    result = await get_user_accounts(1, filters, session)
    
    assert len(result.accounts) == 1
    assert isinstance(result, ListUserAccountSchema)
    session.get_all_by_multiple.assert_awaited_once_with(session, user_id=1)

@pytest.mark.asyncio
async def test_get_user_accounts_empty(setup_data):
    session, _, _ = setup_data
    session.get_all_by_multiple.return_value = []
    filters = QueryAccountFilter()

    result = await get_user_accounts(1, filters, session)
    
    assert len(result.accounts) == 0
    session.get_all_by_multiple.assert_awaited_once_with(session, user_id=1)

@pytest.mark.asyncio
@patch('my_module.generate_user_account_number', return_value='789012')  # Replace 'my_module' with the actual module name
async def test_create_user_account_success(mock_generate, setup_data):
    session, account, account_list = setup_data
    session.get_all_by_multiple.return_value = []
    session.create.return_value = account
    payload = OpenAccountSchema(account_type="checking", initial_deposit=Decimal('100.00'))

    result = await create_user_account(1, payload, session)
    
    assert result.number == '789012'
    assert isinstance(result, UserAccountSchema)
    session.create.assert_awaited_once()
    session.get_all_by_multiple.assert_awaited_once_with(session, user_id=1)

@pytest.mark.asyncio
async def test_create_user_account_exceed_limit(setup_data):
    session, _, account_list = setup_data
    session.get_all_by_multiple.return_value = [Mock()] * USER_MAX_ACCOUNT_LIMIT  # Mock user having max accounts

    payload = OpenAccountSchema(account_type="checking", initial_deposit=Decimal('100.00'))

    with pytest.raises(BadRequest, match="You have exceeded the maximum number of accounts you can create"):
        await create_user_account(1, payload, session)

@pytest.mark.asyncio
async def test_fetch_account_details_by_number_success(setup_data):
    session, account, _ = setup_data
    session.get_one_by_multiple.return_value = account

    result = await fetch_account_details_by_number("123456", 1, session)
    
    assert result.number == "123456"
    assert isinstance(result, UserAccountSchema)
    session.get_one_by_multiple.assert_awaited_once_with(session, **{"number": "123456", "user_id": 1})

@pytest.mark.asyncio
async def test_fetch_account_details_by_number_not_found(setup_data):
    session, _, _ = setup_data
    session.get_one_by_multiple.return_value = None

    with pytest.raises(ObjectNotFound, match="No account with number: 123456 found for this user"):
        await fetch_account_details_by_number("123456", 1, session)
