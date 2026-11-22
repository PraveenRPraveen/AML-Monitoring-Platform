from decimal import Decimal

import pytest

from app.schemas.transactions import TransactionCreate


def test_valid_transaction_schema():
    data = TransactionCreate(
        sender_account_id="00000000-0000-0000-0000-000000000001",
        receiver_account_id="00000000-0000-0000-0000-000000000002",
        amount=Decimal("1250.75"),
        currency="usd",
        transaction_type="TRANSFER",
        occurred_at="2026-11-22T10:30:00Z",
        channel="MOBILE",
        source_location="London, GB",
    )
    assert data.currency == "USD"
    assert data.amount == Decimal("1250.75")


@pytest.mark.parametrize("amount", ["0", "-1", "-99.50"])
def test_negative_or_zero_amount_is_rejected(amount):
    with pytest.raises(ValueError):
        TransactionCreate(
            sender_account_id="00000000-0000-0000-0000-000000000001",
            receiver_account_id="00000000-0000-0000-0000-000000000002",
            amount=amount,
            currency="USD",
            transaction_type="TRANSFER",
            occurred_at="2026-11-22T10:30:00Z",
            channel="MOBILE",
            source_location="London, GB",
        )


def test_timezone_is_required():
    with pytest.raises(ValueError):
        TransactionCreate(
            sender_account_id="00000000-0000-0000-0000-000000000001",
            receiver_account_id="00000000-0000-0000-0000-000000000002",
            amount="10.00",
            currency="USD",
            transaction_type="TRANSFER",
            occurred_at="2026-11-22T10:30:00",
            channel="MOBILE",
            source_location="London, GB",
        )
