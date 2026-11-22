from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.entities import Account, AmlAlert, AuditLog, CaseNote, Customer, FraudAlert, InvestigationCase, Transaction, User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.transactions import TransactionCreate, TransactionResponse
from app.services.transactions import create_transaction, transaction_response

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health():
    return {"status": "healthy", "service": "AML Monitoring Platform"}


@router.get("/customers")
def list_customers(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    customers = db.scalars(select(Customer).limit(limit)).all()
    return [{"id": c.id, "customer_ref": c.customer_ref, "full_name": c.full_name, "segment": c.segment, "country": c.country, "risk_profile": c.risk_profile} for c in customers]


@router.get("/accounts")
def list_accounts(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    accounts = db.scalars(select(Account).limit(limit)).all()
    return [{"id": a.id, "account_number": a.account_number, "customer_id": a.customer_id, "account_type": a.account_type, "currency": a.currency, "balance": str(a.balance), "status": a.status} for a in accounts]


@router.post("/transactions", response_model=TransactionResponse)
def post_transaction(payload: TransactionCreate, response: Response, db: Session = Depends(get_db)):
    try:
        transaction, created = create_transaction(db, payload)
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return transaction_response(transaction, created)


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    account_id: UUID | None = None,
    min_amount: Decimal | None = None,
    db: Session = Depends(get_db),
):
    statement = select(Transaction).order_by(Transaction.occurred_at.desc())
    if account_id:
        statement = statement.where((Transaction.sender_account_id == account_id) | (Transaction.receiver_account_id == account_id))
    if min_amount is not None:
        statement = statement.where(Transaction.amount >= min_amount)
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    transactions = db.scalars(statement).all()
    return [transaction_response(t, False) for t in transactions]


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: UUID, db: Session = Depends(get_db)):
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction_response(transaction, False)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user.id), user.email, user.role)
    return {"access_token": token, "role": user.role}


@router.get("/fraud-alerts")
def fraud_alerts(status_filter: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    statement = select(FraudAlert).order_by(FraudAlert.detected_at.desc())
    if status_filter:
        statement = statement.where(FraudAlert.status == status_filter.upper())
    alerts = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return [{"id": a.id, "transaction_id": a.transaction_id, "risk_score": a.risk_score, "severity": a.severity, "triggered_rules": a.triggered_rules, "explanation": a.explanation, "status": a.status, "detected_at": a.detected_at} for a in alerts]


@router.get("/aml-alerts")
def aml_alerts(status_filter: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    statement = select(AmlAlert).order_by(AmlAlert.detected_at.desc())
    if status_filter:
        statement = statement.where(AmlAlert.status == status_filter.upper())
    alerts = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return [{"id": a.id, "pattern_type": a.pattern_type, "involved_accounts": a.involved_accounts, "related_transactions": a.related_transactions, "explanation": a.explanation, "risk_score": a.risk_score, "status": a.status, "detected_at": a.detected_at} for a in alerts]


@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return {
        "total_transactions": len(db.scalars(select(Transaction)).all()),
        "fraud_alerts": len(db.scalars(select(FraudAlert)).all()),
        "aml_alerts": len(db.scalars(select(AmlAlert)).all()),
        "open_cases": len(db.scalars(select(InvestigationCase).where(InvestigationCase.status.in_(["OPEN", "ASSIGNED", "UNDER_INVESTIGATION"]))).all()),
        "critical_alerts": len(db.scalars(select(FraudAlert).where(FraudAlert.severity == "CRITICAL")).all()),
    }


@router.post("/cases")
def create_case(title: str, source_type: str, source_alert_id: str, priority: str = "MEDIUM", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    import uuid
    try:
        alert_uuid = uuid.UUID(source_alert_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="source_alert_id must be a UUID")
    case = InvestigationCase(title=title, source_type=source_type.upper(), source_alert_id=alert_uuid, priority=priority.upper(), status="OPEN")
    db.add(case)
    db.flush()
    db.add(AuditLog(actor_id=user.id, action="CREATE", entity_type="investigation_case", entity_id=str(case.id), updated_value=title))
    db.commit()
    db.refresh(case)
    return {"id": case.id, "title": case.title, "status": case.status, "priority": case.priority, "source_type": case.source_type}


@router.get("/cases")
def list_cases(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    cases = db.scalars(select(InvestigationCase).order_by(InvestigationCase.created_at.desc())).all()
    return [{"id": c.id, "title": c.title, "source_type": c.source_type, "priority": c.priority, "status": c.status, "assigned_to": c.assigned_to, "outcome": c.outcome, "created_at": c.created_at} for c in cases]


@router.patch("/cases/{case_id}")
def update_case(case_id: str, status_value: str, outcome: str | None = None, assigned_to: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    import uuid
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid case ID")
    case = db.get(InvestigationCase, case_uuid)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    previous = {"status": case.status, "outcome": case.outcome, "assigned_to": str(case.assigned_to) if case.assigned_to else None}
    case.status = status_value.upper().replace(" ", "_")
    if outcome:
        case.outcome = outcome
    if assigned_to:
        try:
            case.assigned_to = uuid.UUID(assigned_to)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid assigned_to UUID")
    db.flush()
    db.add(AuditLog(actor_id=user.id, action="UPDATE", entity_type="investigation_case", entity_id=str(case.id), previous_value=str(previous), updated_value=str({"status": case.status, "outcome": case.outcome, "assigned_to": str(case.assigned_to) if case.assigned_to else None})))
    db.commit()
    db.refresh(case)
    return {"id": case.id, "title": case.title, "status": case.status, "assigned_to": case.assigned_to, "outcome": case.outcome}


@router.post("/cases/{case_id}/notes")
def add_case_note(case_id: str, note: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    import uuid
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid case ID")
    if not db.get(InvestigationCase, case_uuid):
        raise HTTPException(status_code=404, detail="Case not found")
    item = CaseNote(case_id=case_uuid, author_id=user.id, note=note)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "case_id": item.case_id, "note": item.note, "created_at": item.created_at}


@router.get("/audit")
def audit_logs(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(require_admin)):
    logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return [{"id": l.id, "actor_id": l.actor_id, "action": l.action, "entity_type": l.entity_type, "entity_id": l.entity_id, "previous_value": l.previous_value, "updated_value": l.updated_value, "created_at": l.created_at} for l in logs]
