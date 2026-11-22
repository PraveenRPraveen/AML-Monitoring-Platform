# Optional Hadoop/HDFS Batch Extension

This component is intentionally optional. It should not be required by the local Docker MVP.

Recommended pipeline:
1. Export immutable historical transactions from PostgreSQL or Snowflake to object storage.
2. Place exported Parquet/CSV files in HDFS.
3. Use Spark or Hadoop MapReduce to aggregate transaction volume and historical account behavior.
4. Compare batch results with real-time Kafka transaction assessments.

Example HDFS commands:

```bash
hdfs dfs -mkdir -p /aml/raw/transactions
hdfs dfs -put transactions/*.parquet /aml/raw/transactions/
```

The batch pipeline is historical and analytical; Kafka remains responsible for near-real-time event processing.
