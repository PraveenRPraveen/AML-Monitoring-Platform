from decimal import Decimal
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import FraudAlert, Transaction

RULES = {
    "HIGH_VALUE": {"threshold": Decimal("10000.00"), "points": 35},
    "RAPID_TRANSACTIONS": {"limit": 5, "points": 25},
    "UNUSUAL_LOCATION": {"points": 20},
    "FAILED_TRANSACTION": {"points": 15},
}


def severity(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def assess_transaction(db: Session, transaction: Transaction) -> dict:
    triggered = []

    if transaction.amount >= RULES["HIGH_VALUE"]["threshold"]:
        triggered.append({"rule": "HIGH_VALUE", "points": 35, "explanation": "Amount exceeds the high-value threshold."})

    recent = db.scalars(
        select(Transaction)
        .where(Transaction.sender_account_id == transaction.sender_account_id)
        .order_by(desc(Transaction.occurred_at))
        .limit(RULES["RAPID_TRANSACTIONS"]["limit"])
    ).all()
    if len(recent) >= RULES["RAPID_TRANSACTIONS"]["limit"]:
        triggered.append({"rule": "UNUSUAL_FREQUENCY", "points": 25, "explanation": "Multiple recent transactions were observed for the sender."})

    if transaction.source_location.lower().startswith(("unknown", "moscow", "lagos")):
        triggered.append({"rule": "UNUSUAL_LOCATION", "points": 20, "explanation": "Transaction location is outside the expected synthetic customer profile."})

    if transaction.status == "FAILED":
        triggered.append({"rule": "FAILED_TRANSACTION", "points": 15, "explanation": "The transaction failed; repeated failures may indicate fraud testing."})

    score = min(100, sum(rule["points"] for rule in triggered))
    return {
        "transaction_id": str(transaction.id),
        "risk_score": score,
        "risk_category": severity(score),
        "triggered_rules": triggered,
        "explanation": "Synthetic rule-based indicator; not proof of fraud.",
        "detection_timestamp": transaction.created_at.isoformat(),
    }


def persist_fraud_assessment(db: Session, transaction: Transaction) -> dict:
    existing = db.scalar(select(FraudAlert).where(FraudAlert.transaction_id == transaction.id))
    assessment = assess_transaction(db, transaction)
    if existing:
        return assessment
    if assessment["risk_score"] >= 30:
        db.add(FraudAlert(
            transaction_id=transaction.id,
            risk_score=assessment["risk_score"],
            severity=assessment["risk_category"],
            triggered_rules=assessment["triggered_rules"],
            explanation=assessment["explanation"],
        ))
        db.commit()
    return assessment
