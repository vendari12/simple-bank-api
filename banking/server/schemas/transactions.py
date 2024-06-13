from typing import List, Optional
from server.config.settings import settings
from pydantic import BaseModel, ConfigDict
from server.models.enums import TransactionStatus, TransactionType
from server.utils.schema import BaseSchema


class MetaDataSchema(BaseSchema):
    sender: str
    bank: str


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
    metadata: MetaDataSchema

    model_config = ConfigDict(from_attributes=True)


class CreateTransactionSchema(BaseSchema):
    amount: float
    destination_account_number: Optional[str] = None
    source_account_number: str
    tax: float
    type: TransactionType


class PaginatedTransactionSchema(BaseSchema):
    transactions: List[TransactionSchema]
    page: int
    per_page: int
    next_page: Optional[int] = None
    previous_page: Optional[int] = None
