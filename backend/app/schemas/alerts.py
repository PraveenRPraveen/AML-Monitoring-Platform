from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FraudAlertResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    risk_score: int
    severity: str
    triggered_rules: list
    explanation: str
    status: str
    detected_at: datetime


class AmlAlertResponse(BaseModel):
    id: UUID
    pattern_type: str
    involved_accounts: list
    related_transactions: list
    explanation: str
    risk_score: int
    status: str
    detected_at: datetime
