import logging
from abc import ABC, abstractmethod
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from server.models.accounts import Account, Transaction


class TransactionStrategy(ABC):
    """Abstract base class for transaction strategies."""

    @abstractmethod
    async def execute(self):
        """Execute the transaction."""
        pass


# Step 2: Implement Concrete Strategies
class CreditTransaction(TransactionStrategy):
    """Strategy for processing credit transactions."""

    async def execute(
        self,
        transaction: Transaction,
        account: Account,
        metadata: Dict,
        session: AsyncSession,
    ):
        # Implement credit logic here, e.g., update account balance
        logging.info(
            f"Processing credit of {transaction.amount} {transaction.currency} for account {transaction.account_id}"
        )

        # Example implementation:
        transaction.account.balance += transaction.amount
        # Update any other related metadata or logs


class WithdrawalTransaction(TransactionStrategy):
    """Strategy for processing withdrawal transactions."""

    async def execute(self, transaction: Transaction):
        # Implement withdrawal logic here, e.g., update account balance
        logging.info(
            f"Processing withdrawal of {transaction.amount} {transaction.currency} for account {transaction.account_id}"
        )
        if transaction.account.balance < transaction.amount:
            raise ValueError("Insufficient funds")
        transaction.account.balance -= transaction.amount
        # Update any other related metadata or logs


class TransferTransaction(TransactionStrategy):
    """Strategy for processing transfer transactions."""

    async def execute(self, transaction: Transaction):
        # Implement transfer logic here, e.g., update balances of involved accounts
        logging.info(
            f"Processing transfer of {transaction.amount} {transaction.currency} from account {transaction.account_id} to {transaction.metadata.get('target_account_id')}"
        )
        source_account = transaction.account
        target_account_id = transaction.metadata.get("target_account_id")
        if not target_account_id:
            raise ValueError("Target account ID must be specified for transfers")

        # Assuming session is a database session object available for querying
        target_account = await session.get(Account, target_account_id)
        if source_account.balance < transaction.amount:
            raise ValueError("Insufficient funds")

        source_account.balance -= transaction.amount
        target_account.balance += transaction.amount
        # Update any other related metadata or logs


# Step 3: Implement the Factory Pattern
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


class TransactionStrategy(ABC):
    """Abstract base class for transaction strategies."""

    @abstractmethod
    async def execute(self, transaction: Transaction):
        """Execute the transaction."""
        pass


# Step 2: Implement Concrete Strategies
class CreditTransaction(TransactionStrategy):
    """Strategy for processing credit transactions."""

    async def execute(self, transaction: Transaction):
        # Implement credit logic here, e.g., update account balance
        logging.info(
            f"Processing credit of {transaction.amount} {transaction.currency} for account {transaction.account_id}"
        )
        # Example implementation:
        transaction.account.balance += transaction.amount
        # Update any other related metadata or logs


class WithdrawalTransaction(TransactionStrategy):
    """Strategy for processing withdrawal transactions."""

    async def execute(self, transaction: Transaction):
        # Implement withdrawal logic here, e.g., update account balance
        logging.info(
            f"Processing withdrawal of {transaction.amount} {transaction.currency} for account {transaction.account_id}"
        )
        if transaction.account.balance < transaction.amount:
            raise ValueError("Insufficient funds")
        transaction.account.balance -= transaction.amount
        # Update any other related metadata or logs


class TransferTransaction(TransactionStrategy):
    """Strategy for processing transfer transactions."""

    async def execute(self, transaction: Transaction):
        # Implement transfer logic here, e.g., update balances of involved accounts
        logging.info(
            f"Processing transfer of {transaction.amount} {transaction.currency} from account {transaction.account_id} to {transaction.metadata.get('target_account_id')}"
        )
        source_account = transaction.account
        target_account_id = transaction.metadata.get("target_account_id")
        if not target_account_id:
            raise ValueError("Target account ID must be specified for transfers")

        # Assuming session is a database session object available for querying
        target_account = await session.get(Account, target_account_id)
        if source_account.balance < transaction.amount:
            raise ValueError("Insufficient funds")

        source_account.balance -= transaction.amount
        target_account.balance += transaction.amount
        # Update any other related metadata or logs


# Step 3: Implement the Factory Pattern
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
