import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from server.controllers.transactions import (Account, BadRequest,
                                             process_transaction_in_background,
                                             schedule_transaction)
from server.utils.queues import process_tasks, task_queue
from server.utils.strategies import (CreditTransaction, TransactionFactory,
                                     TransactionStatus, TransactionType,
                                     TransferTransaction,
                                     WithdrawalTransaction)


@pytest.mark.asyncio
@patch("server.utils.cache.RedisLock", AsyncMock())
async def test_credit_transaction(db_session, sample_account, sample_account_transaction):
    sample_account_transaction.type = TransactionType.CREDIT

    strategy = CreditTransaction()
    await strategy.execute(sample_account_transaction, sample_account, {}, db_session)

    sample_account.credit_account.assert_awaited_with(sample_account_transaction.amount, db_session)
    assert sample_account_transaction.status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
@patch("server.utils.cache.RedisLock", AsyncMock())
async def test_withdrawal_transaction(db_session, sample_account, sample_account_transaction):
    db_session, account, transaction = db_session, sample_account, sample_account_transaction
    transaction.type = TransactionType.WITHDRAWAL

    strategy = WithdrawalTransaction()
    await strategy.execute(transaction, account, {}, db_session)

    account.debit_account.assert_awaited_with(transaction.amount, db_session)
    assert account.debit_account.call_count == 1
    assert transaction.status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
@patch("server.utils.cache.RedisLock", AsyncMock())
async def test_withdrawal_transaction_insufficient_funds(db_session, sample_account, sample_account_transaction):
    db_session, account, transaction = db_session, sample_account, sample_account_transaction
    transaction.type = TransactionType.WITHDRAWAL
    account.balance = 40.00

    strategy = WithdrawalTransaction()
    with pytest.raises(BadRequest, match="Insufficient funds"):
        await strategy.execute(transaction, account, {}, db_session)


@pytest.mark.asyncio
@patch("server.utils.cache.RedisLock", AsyncMock())
@patch("server.models.accounts.Account.credit_account", AsyncMock())
async def test_transfer_transaction(db_session, sample_account, sample_account_transaction):
    db_session, account, transaction = db_session, sample_account, sample_account_transaction
    transaction.type = TransactionType.TRANSFER
    transaction.metadata = {"target_account_number": "target_account"}
    target_account = AsyncMock(spec=Account)
    target_account.balance = 1000
    transaction.target_account = target_account

    with patch.object(db_session, "get", return_value=target_account):
        strategy = TransferTransaction()
        await strategy.execute(transaction, account, transaction.metadata, db_session)

        account.debit_account.assert_awaited_with(transaction.amount, db_session)
        target_account.credit_account.assert_awaited_with(transaction.amount, db_session)
        assert transaction.status == TransactionStatus.COMPLETED


def test_transaction_factory():
    assert isinstance(
        TransactionFactory.create(TransactionType.CREDIT), CreditTransaction
    )
    assert isinstance(
        TransactionFactory.create(TransactionType.WITHDRAWAL), WithdrawalTransaction
    )
    assert isinstance(
        TransactionFactory.create(TransactionType.TRANSFER), TransferTransaction
    )
    with pytest.raises(BadRequest):
        TransactionFactory.create("UNKNOWN_TYPE")


@pytest.mark.asyncio
@patch("server.utils.cache.RedisLock", AsyncMock())
async def test_transaction_scheduling(db_session, sample_account, sample_account_transaction):
    db_session, account, transaction = db_session, sample_account, sample_account_transaction
    transaction.type = TransactionType.CREDIT

    schedule_transaction(transaction, account, {}, db_session)

    await asyncio.sleep(0.1)  # Give some time for the task to be queued
    assert not task_queue.empty()


@pytest.mark.asyncio
@patch("server.utils.cache.RedisLock", AsyncMock())
async def test_task_processing(db_session, sample_account, sample_account_transaction):
    db_session, account, transaction = db_session, sample_account, sample_account_transaction
    transaction.type = TransactionType.CREDIT

    schedule_transaction(transaction, account, {}, db_session)
    await process_tasks()  # Process the queue

    account.credit_account.assert_awaited_with(transaction.amount, db_session)
    assert transaction.status == TransactionStatus.COMPLETED
