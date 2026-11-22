from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCreate(BaseModel):
    event_id: str | None = Field(default=None, max_length=64)
    sender_account_id: UUID
    receiver_account_id: UUID
    customer_id: UUID | None = None
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    transaction_type: Literal["PAYMENT", "TRANSFER", "WITHDRAWAL", "DEPOSIT"]
    occurred_at: datetime
    channel: Literal["MOBILE", "ONLINE", "ATM", "BRANCH", "POS"]
    source_location: str = Field(min_length=2, max_length=100)
    device_id: UUID | None = None
    beneficiary_id: UUID | None = None
    status: Literal["COMPLETED", "PENDING", "FAILED"] = "COMPLETED"

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, value: str) -> str:
        return value.upper()

    @field_validator("occurred_at")
    @classmethod
    def timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transaction_id: UUID
    event_id: str
    customer_id: UUID
    sender_account_id: UUID
    receiver_account_id: UUID
    amount: Decimal
    currency: str
    transaction_type: str
    occurred_at: datetime
    channel: str
    source_location: str
    status: str
    processing_status: str
    created: bool = False
