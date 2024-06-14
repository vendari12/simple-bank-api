from typing import Dict

from server.models.enums import AccountLevel, AccountType
from server.utils.accounts import generate_user_account_number


def generate_account_data(
    type: AccountType = AccountType.CHECKINGS, level: AccountLevel = AccountLevel.BASIC
) -> Dict[str, str]:
    return {
        "number": generate_user_account_number(),
        "type": type,
        "level": level,
        "currency": "USD",
    }
