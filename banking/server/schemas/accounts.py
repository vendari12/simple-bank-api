from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from server.models.enums import AccountLevel, AccountStatus, AccountType
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
    id: int

    model_config = ConfigDict(from_attributes=True)


class CloseAccountRequest(BaseSchema):
    account_id: int
    reasons: str


class OpenAccountSchema(BaseSchema):
    type: AccountType
    level: AccountLevel


class ListUserAccountSchema(BaseSchema):
    account: Optional[List[UserAccountSchema]] = None
    user_id: int


class QueryAccountFilter(BaseSchema):
    status: Optional[AccountStatus] = None
    level: Optional[AccountLevel] = None
    type: Optional[AccountType] = None
