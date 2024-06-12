from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from server.models.enums import AccountLevel, AccountType
from server.utils.schema import BaseSchema


class UserAccountSchema(BaseSchema):
    number: str
    type: AccountType
    currency: str
    balance: float
    created_at: datetime
    updated_at: datetime
    user_id: int
    level: AccountLevel

    model_config = ConfigDict(from_attributes=True)


class ListUserAccountSchema(BaseSchema):
    accounts: List[UserAccountSchema]
