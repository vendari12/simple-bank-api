from typing import Any, Dict

from server.models.enums import TransactionType
from server.utils.transactions import generate_transaction_code


def generate_transaction(
    account_id: int, type: TransactionType, sender: str
) -> Dict[str, Any]:
    description = f"{type} on account by {sender}"
    return {
        "account_id": account_id,
        "amount": 1000,
        "description": description,
        "extra": {"description": description, "sender": sender},
        "code": generate_transaction_code(account_id, type),
    }
