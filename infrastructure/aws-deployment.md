# AWS Deployment Guide

## Recommended staging architecture

- ECS Fargate: FastAPI, React/Nginx and simulator containers.
- RDS PostgreSQL: operational database.
- MSK: managed Kafka.
- S3: exports and analytical snapshots.
- CloudWatch: logs and metrics.
- Secrets Manager: JWT secret, database credentials and API keys.
- Application Load Balancer: HTTPS ingress.

## Secrets

Do not use `.env.local` in AWS. Configure ECS task secrets from Secrets Manager.

## Database

Create RDS PostgreSQL and set `DATABASE_URL`. Run Alembic migrations as a one-shot ECS task before deployment.

## Observability

Forward FastAPI and simulator logs to CloudWatch. Add alarms for API latency, database connections, consumer lag and dead-letter topic size.
