# Phase 1: Foundation

## Components

- `backend`: FastAPI application, Pydantic schemas, SQLAlchemy models and REST routes.
- `database`: Alembic migration and synthetic seed data.
- `transaction-simulator`: HTTP batch or continuous synthetic transaction generator.
- `postgres`: Operational data source.

## Communication

The simulator calls FastAPI using HTTP. FastAPI validates the payload and writes it to PostgreSQL. Alert and streaming systems are not active in this phase.

## Idempotency

The `event_id` field has a unique database constraint. Repeated event delivery returns the existing transaction and does not create a duplicate.

## Monetary Integrity

Monetary fields use `NUMERIC(18,2)`. JSON payloads represent money as decimal strings. Pydantic validates positive values.

## Synthetic Data

All seeded identities, account numbers and devices are synthetic and must not be interpreted as real-world records.
