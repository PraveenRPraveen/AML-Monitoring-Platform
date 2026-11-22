# Kafka Topics

| Topic | Purpose |
|---|---|
| bank.transactions | Validated transaction events |
| bank.fraud.alerts | Fraud assessment output |
| bank.aml.alerts | AML pattern indicators |
| bank.transaction.results | Processing outcome |
| bank.dead-letter | Invalid or repeatedly failing events |

Retained events support replay. Consumers must use stable consumer groups and commit offsets only after a database operation succeeds. The application currently uses idempotency keys; exactly-once semantics are not claimed.
