from typing import List, Optional, Dict

from pydantic import ConfigDict
from server.config.settings import settings
from server.models.enums import TransactionStatus, TransactionType
from server.utils.schema import BaseSchema


class FilterTransactionSchema(BaseSchema):
    type: TransactionType
    status: TransactionStatus
    account_number: str
    page: int = 1
    per_page: int = settings.PAGE_SIZE

class TransactionSchema(BaseSchema):
    code: str
    type: TransactionType
    amount: float
    description: str
    currency: str
    user_id: int
    status: TransactionStatus
    extra: Dict

    model_config = ConfigDict(from_attributes=True)



class RequestTransactionSchema(BaseSchema):
    amount: float
    destination_account_number: Optional[str] = None
    source_account_number: str
    tax: float
    type: TransactionType

class CreateTransactionSchema(BaseSchema):
    amount: float
    account_id: int
    description: str
    tax: float
    type: TransactionType
    currency: str
    source: str
    extra: dict

class PaginatedTransactionSchema(BaseSchema):
    transactions: List[TransactionSchema]
    page: int
    per_page: int
    next_page: Optional[int] = None
    previous_page: Optional[int] = None
