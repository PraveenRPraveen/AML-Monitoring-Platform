import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Account, Transaction
from app.schemas.transactions import TransactionCreate


class TransactionDuplicateError(Exception):
    pass


def create_transaction(db: Session, payload: TransactionCreate) -> tuple[Transaction, bool]:
    sender = db.scalar(select(Account).where(Account.id == payload.sender_account_id))
    receiver = db.scalar(select(Account).where(Account.id == payload.receiver_account_id))
    if not sender or not receiver:
        raise LookupError("Sender or receiver account does not exist")

    event_id = payload.event_id or f"evt_{uuid.uuid4()}"
    existing = db.scalar(select(Transaction).where(Transaction.event_id == event_id))
    if existing:
        return existing, False

    customer_id = payload.customer_id or sender.customer_id
    if sender.customer_id != customer_id:
        raise ValueError("Customer ID does not match the sender account")

    if payload.occurred_at > datetime.now(timezone.utc):
        raise ValueError("occurred_at cannot be in the future")

    transaction = Transaction(
        event_id=event_id,
        sender_account_id=sender.id,
        receiver_account_id=receiver.id,
        customer_id=customer_id,
        amount=payload.amount,
        currency=payload.currency,
        transaction_type=payload.transaction_type,
        occurred_at=payload.occurred_at.replace(tzinfo=None),
        channel=payload.channel,
        source_location=payload.source_location,
        device_id=payload.device_id,
        beneficiary_id=payload.beneficiary_id,
        status=payload.status,
        processing_status="RECEIVED",
    )

    db.add(transaction)
    db.flush()

    if payload.status == "COMPLETED":
        sender.balance -= payload.amount
        receiver.balance += payload.amount

    db.commit()
    db.refresh(transaction)

    from app.services.aml_engine import persist_aml_assessments
    from app.services.fraud_engine import persist_fraud_assessment
    persist_fraud_assessment(db, transaction)
    persist_aml_assessments(db, transaction)
    return transaction, True


def transaction_response(transaction: Transaction, created: bool = False):
    return {
        "transaction_id": transaction.id,
        "event_id": transaction.event_id,
        "customer_id": transaction.customer_id,
        "sender_account_id": transaction.sender_account_id,
        "receiver_account_id": transaction.receiver_account_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "transaction_type": transaction.transaction_type,
        "occurred_at": transaction.occurred_at,
        "channel": transaction.channel,
        "source_location": transaction.source_location,
        "status": transaction.status,
        "processing_status": transaction.processing_status,
        "created": created,
    }
