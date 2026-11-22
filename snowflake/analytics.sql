CREATE SCHEMA IF NOT EXISTS AML_ANALYTICS;

CREATE OR REPLACE TABLE AML_ANALYTICS.DAILY_TRANSACTION_SUMMARY AS
SELECT CAST(occurred_at AS DATE) AS transaction_date,
       currency,
       COUNT(*) AS transaction_count,
       SUM(amount) AS transaction_volume
FROM AML_RAW.TRANSACTIONS
GROUP BY 1,2;

CREATE OR REPLACE TABLE AML_ANALYTICS.ACCOUNT_RISK_SUMMARY AS
SELECT sender_account_id,
       COUNT(*) AS transaction_count,
       SUM(amount) AS total_sent
FROM AML_RAW.TRANSACTIONS
GROUP BY sender_account_id;
