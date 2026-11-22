from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AmlAlert, Transaction


def detect_aml_patterns(db: Session, transaction: Transaction) -> list[dict]:
    alerts = []
    cutoff = transaction.occurred_at - timedelta(hours=24)
    history = db.scalars(select(Transaction).where(Transaction.occurred_at >= cutoff).order_by(Transaction.occurred_at)).all()

    incoming = [t for t in history if t.receiver_account_id == transaction.receiver_account_id]
    if len(incoming) >= 5:
        senders = {str(t.sender_account_id) for t in incoming}
        if len(senders) >= 5:
            alerts.append(make_alert("MANY_TO_ONE", [str(transaction.receiver_account_id)], [str(t.id) for t in incoming],
                "Multiple accounts transferred funds to the same destination within 24 hours.", 75))

    outgoing = [t for t in history if t.sender_account_id == transaction.sender_account_id]
    if len(outgoing) >= 5:
        alerts.append(make_alert("STRUCTURING", [str(transaction.sender_account_id)], [str(t.id) for t in outgoing],
            "Repeated smaller transactions may indicate structuring, but require investigation.", 68))

    rapid = [t for t in history if t.receiver_account_id == transaction.receiver_account_id and t.sender_account_id == transaction.sender_account_id]
    if len(rapid) >= 3:
        alerts.append(make_alert("RAPID_FUND_MOVEMENT", [str(transaction.sender_account_id), str(transaction.receiver_account_id)],
            [str(t.id) for t in rapid], "Repeated rapid movement was detected between two accounts.", 70))

    by_receiver = defaultdict(list)
    for item in history:
        by_receiver[str(item.receiver_account_id)].append(item)
    for receiver, items in by_receiver.items():
        sender_ids = {str(item.sender_account_id) for item in items}
        if receiver in sender_ids:
            alerts.append(make_alert("CIRCULAR_TRANSACTION", [receiver], [str(item.id) for item in items],
                "An account relationship indicates a possible circular transaction path.", 82))

    return alerts


def make_alert(pattern_type: str, accounts: list[str], transactions: list[str], explanation: str, score: int) -> dict:
    return {
        "pattern_type": pattern_type,
        "involved_accounts": accounts,
        "related_transactions": transactions,
        "explanation": explanation,
        "risk_score": score,
    }


def persist_aml_assessments(db: Session, transaction: Transaction) -> list[dict]:
    alerts = detect_aml_patterns(db, transaction)
    for alert in alerts:
        exists = db.scalar(select(AmlAlert).where(
            AmlAlert.pattern_type == alert["pattern_type"],
            AmlAlert.status == "NEW",
        ))
        if not exists:
            db.add(AmlAlert(**alert))
    db.commit()
    return alerts
