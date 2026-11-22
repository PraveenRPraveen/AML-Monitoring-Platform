import json
import os
import time
import uuid

from confluent_kafka import Producer

TOPIC = os.getenv("KAFKA_TOPIC", "bank.transactions")
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

producer = Producer({"bootstrap.servers": BOOTSTRAP, "enable.idempotence": True, "acks": "all"})


def delivery_report(error, message):
    if error:
        print(f"Delivery failed: {error}")
    else:
        print(f"Delivered to {message.topic()} [{message.partition()}]")


def publish(transaction: dict):
    transaction.setdefault("event_id", f"evt_{uuid.uuid4()}")
    producer.produce(TOPIC, key=transaction["event_id"], value=json.dumps(transaction).encode(), on_delivery=delivery_report)
    producer.flush()
