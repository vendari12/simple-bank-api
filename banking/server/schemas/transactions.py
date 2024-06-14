from typing import List, Optional, Dict
from uuid import UUID
from pydantic import ConfigDict, BaseModel, field_validator
from server.config.settings import settings
from server.models.enums import TransactionStatus, TransactionType
from server.utils.schema import BaseSchema


class FilterTransactionSchema(BaseSchema):
    type: Optional[TransactionType] =None
    status: Optional[TransactionStatus] =None
    account_number: str
    page: int = 1
    per_page: int = settings.PAGE_SIZE

class TransactionSchema(BaseModel):
    code: UUID
    type: TransactionType
    amount: float
    description: str
    currency: str
    account_id: int
    status: TransactionStatus
    extra: Dict

    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('currency', mode="before")
    @classmethod
    def parse_currency(cls, value):
        if not isinstance(value, str):
            return value.name
        return value



class RequestTransactionSchema(BaseSchema):
    amount: float
    destination_account_number: Optional[str] = None
    source_account_number: str
    tax: float
    currency: str
    type: TransactionType

class CreateTransactionSchema(BaseSchema):
    amount: float
    account_id: int
    description: str
    type: TransactionType
    currency: str
    extra: dict

class PaginatedTransactionSchema(BaseSchema):
    transactions: List[TransactionSchema]
    page: int
    per_page: int
    next_page: Optional[int] = None
    previous_page: Optional[int] = None
