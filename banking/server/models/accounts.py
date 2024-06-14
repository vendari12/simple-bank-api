from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Self, Tuple

from server.utils.cache import construct_resource_lock_key
from server.utils.constants import DEFAULT_CASCADE_MODE, SIGNUP_ACCOUNT_TOPUP
from server.utils.db import BaseModel
from server.utils.transactions import generate_transaction_code
from sqlalchemy import (DECIMAL, JSON, UUID, Enum, ForeignKey, String, Text,
                        Uuid)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import CurrencyType

from .enums import (AccountLevel, AccountStatus, AccountType,
                    TransactionStatus, TransactionType)


class Account(BaseModel):
    """Represents a bank account."""

    __tablename__ = "accounts"

    number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        DECIMAL(20, 2), default=Decimal(SIGNUP_ACCOUNT_TOPUP)
    )
    level: Mapped[AccountLevel] = mapped_column(
        Enum(AccountLevel), index=True, default=AccountLevel.BASIC
    )
    currency: Mapped[str] = mapped_column(CurrencyType, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.ACTIVE
    )

    def __repr__(self) -> str:
        return (
            f"<Account(number={self.number}, type={self.type}, balance={self.balance})>"
        )

    @property
    def lock_key(self) -> str:
        return construct_resource_lock_key(self)

    async def credit_account(self, amount: float, session: AsyncSession) -> Self:
        """Credit a users account

        Args:
            amount (float): Amount to be credited
            session (AsyncSession): DB session

        Returns:
            Self: Account instance
        """
        self.balance += amount
        session.add(self)
        return self

    async def debit_account(self, amount: float, session: AsyncSession) -> Self:
        """Debits a users account

        Args:
            amount (float): Amount to be debitted
            session (AsyncSession): DB session

        Returns:
            Self: Account instance
        """
        self.balance -= amount
        session.add(self)
        return self

    async def update_transaction_status(
        self, code: str, status: TransactionStatus, session: AsyncSession
    ) -> Tuple[Optional["Transaction"], bool]:
        exists = True
        transaction = await Transaction.get_one_by_multiple(
            session, **{"account_id": self.id, "code": code}
        )
        if transaction:
            transaction.status = status
            session.add(transaction)
            return transaction, exists
        return None, not exists

    async def create_transaction(
        self,
        session: AsyncSession,
        metadata: Dict,
        type: TransactionType,
        amount: float,
        status: TransactionStatus,
        currency: str,
    ):
        code = generate_transaction_code(
            str(self.id), str(self.number), datetime.now(datetime.UTC).isoformat()
        )
        return await Transaction.create(
            session,
            **{
                "type": type,
                "status": status,
                "currency": currency,
                "amount": amount,
                "metadata": metadata,
                "code": code,
            },
        )


class Transaction(BaseModel):
    """Represents a financial transaction."""

    __tablename__ = "transactions"
    code: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    currency: Mapped[str] = mapped_column(CurrencyType)
    account = relationship("Account", back_populates="transactions")
    extra: Mapped[Dict] = mapped_column(JSON)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING
    )

    def __repr__(self) -> str:
        return f"<Transaction(type={self.type}, amount={self.amount})>"
