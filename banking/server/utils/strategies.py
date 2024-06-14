import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from server.models.accounts import (Account, Transaction, TransactionStatus,
                                    TransactionType)
from server.utils.cache import (RedisLock, construct_resource_lock_key,
                                get_redis_client)
from server.utils.exceptions import BadRequest
from sqlalchemy.ext.asyncio import AsyncSession


# Abstract Base Class for transaction strategies
class TransactionStrategy(ABC):
    """Abstract base class for transaction strategies."""

    @abstractmethod
    async def execute(
        self,
        transaction: Transaction,
        account: Account,
        metadata: Dict,
        session: AsyncSession,
    ):
        """Execute the transaction."""
        pass


# Credit Transaction Strategy
class CreditTransaction(TransactionStrategy):
    """Strategy for processing credit transactions."""

    async def execute(
        self,
        transaction: Transaction,
        account: Account,
        metadata: Dict,
        session: AsyncSession,
    ):
        logging.info(
            f"Processing credit of {transaction.amount} {transaction.currency} for account {account.number}"
        )
        
        # Ensure resource locking to prevent concurrent balance updates
        lock_key = account.lock_key
        redis_client = get_redis_client()
        
        async with RedisLock(redis_client, lock_key):
            await account.credit_account(transaction.amount, session)
            transaction.status = TransactionStatus.COMPLETED
            await session.commit()


# Withdrawal Transaction Strategy
class WithdrawalTransaction(TransactionStrategy):
    """Strategy for processing withdrawal transactions."""

    async def execute(
        self,
        transaction: Transaction,
        account: Account,
        metadata: Dict,
        session: AsyncSession,
    ):
        logging.info(
            f"Processing withdrawal of {transaction.amount} {transaction.currency} for account {account.number}"
        )
        
        lock_key = construct_resource_lock_key(account)
        redis_client = get_redis_client()

        async with RedisLock(redis_client, lock_key):
            if account.balance < transaction.amount:
                raise BadRequest("Insufficient funds")
            
            await account.debit_account(transaction.amount, session)
            transaction.status = TransactionStatus.COMPLETED
            
            await session.commit()


# Transfer Transaction Strategy
class TransferTransaction(TransactionStrategy):
    """Strategy for processing transfer transactions."""

    async def execute(
        self,
        transaction: Transaction,
        account: Account,
        metadata: Dict,
        session: AsyncSession,
    ):
        logging.info(
            f"Processing transfer of {transaction.amount} {transaction.currency} from account {account.number} to {metadata.get('target_account_number')}"
        )

        target_account_number = metadata.get("target_account_number")
        if not target_account_number:
            raise BadRequest("Target account number must be specified for transfers")
        
        target_account = await session.get(Account, {"number": target_account_number})
        if not target_account:
            raise BadRequest("Target account not found")

        source_lock_key = construct_resource_lock_key(account)
        target_lock_key = construct_resource_lock_key(target_account)
        redis_client = get_redis_client()

        async with RedisLock(redis_client, source_lock_key), RedisLock(redis_client, target_lock_key):
            if account.balance < transaction.amount:
                raise BadRequest("Insufficient funds")

            await account.debit_account(transaction.amount, session)
            await target_account.credit_account(transaction.amount, session)
            transaction.status = TransactionStatus.COMPLETED
            await session.commit()


class TransactionFactory:
    """Factory for creating transaction strategies."""

    @staticmethod
    def create(transaction_type: TransactionType) -> TransactionStrategy:
        if transaction_type == TransactionType.CREDIT:
            return CreditTransaction()
        elif transaction_type == TransactionType.WITHDRAWAL:
            return WithdrawalTransaction()
        elif transaction_type == TransactionType.TRANSFER:
            return TransferTransaction()
        else:
            raise ValueError(f"Unknown transaction type: {transaction_type}")