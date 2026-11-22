from datetime import datetime, timedelta
import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import Account, Customer, Device, User
from app.core.security import hash_password


def seed():
    db = SessionLocal()
    try:
        if db.scalar(select(Customer).limit(1)):
            return

        customers = []
        accounts = []
        for index in range(1, 11):
            customer = Customer(
                customer_ref=f"CUS-{1000 + index}",
                full_name=f"Synthetic Customer {index}",
                segment="RETAIL" if index % 3 else "BUSINESS",
                country=["GB", "US", "DE", "FR"][index % 4],
                risk_profile=["LOW", "MEDIUM", "HIGH"][index % 3],
                onboarding_date=datetime.utcnow() - timedelta(days=100 + index * 30),
            )
            db.add(customer)
            db.flush()
            for account_index in range(2):
                account = Account(
                    account_number=f"SYN-{10000 + index * 10 + account_index}",
                    customer_id=customer.id,
                    account_type="CURRENT" if account_index == 0 else "SAVINGS",
                    currency="USD",
                    balance=10000 + index * 750,
                    status="ACTIVE",
                )
                db.add(account)
                accounts.append(account)
            customers.append(customer)

        db.add(Device(device_identifier="SYN-DEVICE-001", device_type="MOBILE"))
        db.add(Device(device_identifier="SYN-DEVICE-002", device_type="DESKTOP"))
        db.add(User(email="analyst@aml.local", full_name="Synthetic Fraud Analyst", password_hash=hash_password("Analyst123!"), role="ANALYST"))
        db.add(User(email="admin@aml.local", full_name="Synthetic Administrator", password_hash=hash_password("Admin123!"), role="ADMIN"))
        db.commit()
        print("Seeded 10 synthetic customers, 20 accounts, and default analyst and administrator accounts")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
