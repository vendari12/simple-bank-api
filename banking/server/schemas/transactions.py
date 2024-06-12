from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from server.models.enums import TransactionStatus, TransactionType
from server.utils.schema import BaseSchema


class MetaDataSchema(BaseSchema):
    sender: str
    bank: str
    
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
    destination_account_number: str
    source_account_number: str
    tax: float
    type: TransactionType

class PaginatedTransactionSchema(BaseSchema):
    transactions: List[TransactionSchema]
    page: int
    per_page: int
    next_page: Optional[int] = None
    previous_page: Optional[int] = None