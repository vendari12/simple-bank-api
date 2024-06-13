from enum import Enum


class TokenTypeEnum(str, Enum):
    EMAIL_CHANGE = "email-change"
    ACCOUNT_CONFIRM = "account-confirm"
    PASSWORD_RESET = "password-reset"


class AccountLevel(str, Enum):
    REGULAR = "regular"
    PREMUIM = "premuim"
    BASIC = "Basic"


class UserRole(str, Enum):
    """Enumeration for different user roles in the bank."""

    CUSTOMER = "customer"
    ADMIN = "admin"
    EMPLOYEE = "employee"


class TransactionType(str, Enum):
    """Enumeration for different types of transactions."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"


class TransactionStatus(str, Enum):
    """Enumeration for different types status of a transaction."""

    FAILED = "failed"
    SUCCESS = "success"
    PENDING = "pending"


class CardType(str, Enum):
    """Enumeration for different types of cards."""

    DEBIT = "debit"
    CREDIT = "credit"


class LoanStatus(str, Enum):
    """Enumeration for the status of a loan."""

    ACTIVE = "active"
    CLOSED = "closed"
    DEFAULTED = "defaulted"


class AccountStatus(str, Enum):
    """Enumeration for the status of a user account."""

    ACTIVE = "active"
    CLOSED = "closed"
    ON_HOLD = "on hold"


class AccountType(str, Enum):
    """Enumeration for different types of bank accounts."""

    CHECKINGS = "checkings"
    SAVINGS = "savings"
    CURRENT = "current"
    DOMICILIARY = "domiciliary"
