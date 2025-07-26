from pydantic import BaseModel,Field
import uuid
from enum import Enum

class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderItemSchemaCreate(BaseModel,extra='forbid'):
    book_id:uuid.UUID
    quantity:int = Field(...,ge=1)
    order_status : OrderStatusEnum

class OrderItemCreateRequest(BaseModel):
    items:list[OrderItemSchemaCreate]

class OrderPlaceSuccessfully(BaseModel):
    success:str


 