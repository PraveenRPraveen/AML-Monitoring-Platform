import os
import random
import time
import uuid
from datetime import datetime, timezone

import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
MODE = os.getenv("MODE", "batch").lower()
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "25"))
INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "2"))

LOCATIONS = ["London, GB", "New York, US", "Berlin, DE", "Paris, FR", "Dubai, AE", "Singapore, SG"]
CHANNELS = ["MOBILE", "ONLINE", "ATM", "BRANCH", "POS"]
TYPES = ["PAYMENT", "TRANSFER", "WITHDRAWAL", "DEPOSIT"]


def fetch_entities(client: httpx.Client):
    accounts = client.get("/api/v1/accounts").raise_for_status().json()
    devices = client.get("/api/v1/devices").json() if False else []
    return accounts


def normal_transaction(accounts):
    sender, receiver = random.sample(accounts, 2)
    return {
        "event_id": f"evt_{uuid.uuid4()}",
        "sender_account_id": sender["id"],
        "receiver_account_id": receiver["id"],
        "customer_id": sender["customer_id"],
        "amount": f"{random.uniform(10, 950):.2f}",
        "currency": sender["currency"],
        "transaction_type": random.choice(TYPES),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "channel": random.choice(CHANNELS),
        "source_location": random.choice(LOCATIONS),
        "status": "COMPLETED",
    }


def suspicious_transaction(accounts):
    sender, receiver = random.sample(accounts, 2)
    scenario = random.choice(["HIGH_VALUE", "RAPID", "UNUSUAL_LOCATION", "FAILED"])
    amount = random.uniform(15000, 50000) if scenario == "HIGH_VALUE" else random.uniform(900, 4500)
    location = random.choice(["Unknown, XX", "Lagos, NG", "Moscow, RU"]) if scenario == "UNUSUAL_LOCATION" else random.choice(LOCATIONS)
    status_value = "FAILED" if scenario == "FAILED" else "COMPLETED"
    return {
        "event_id": f"evt_{uuid.uuid4()}",
        "sender_account_id": sender["id"],
        "receiver_account_id": receiver["id"],
        "customer_id": sender["customer_id"],
        "amount": f"{amount:.2f}",
        "currency": sender["currency"],
        "transaction_type": "TRANSFER",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "channel": random.choice(CHANNELS),
        "source_location": location,
        "status": status_value,
    }


def generate_batch(client: httpx.Client, size: int):
    accounts = fetch_entities(client)
    if len(accounts) < 2:
        print("Simulator needs at least two accounts; seed data is not available yet")
        return
    for _ in range(size):
        payload = suspicious_transaction(accounts) if random.random() < 0.25 else normal_transaction(accounts)
        response = client.post("/api/v1/transactions", json=payload)
        if response.is_success:
            body = response.json()
            print(f"Generated {body['transaction_id']} amount={body['amount']} status={body['status']}")
        else:
            print(f"Rejected transaction: {response.status_code} {response.text}")


def main():
    for attempt in range(30):
        try:
            with httpx.Client(base_url=API_BASE_URL, timeout=10) as client:
                client.get("/api/v1/health").raise_for_status()
                if MODE == "continuous":
                    while True:
                        generate_batch(client, BATCH_SIZE)
                        time.sleep(INTERVAL_SECONDS)
                generate_batch(client, BATCH_SIZE)
                return
        except httpx.HTTPError:
            print(f"Waiting for API ({attempt + 1}/30)...")
            time.sleep(2)
    raise RuntimeError("Backend API did not become available")


if __name__ == "__main__":
    main()
