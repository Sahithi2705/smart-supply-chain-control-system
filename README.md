\# Smart Supply Chain Control Tower



A production-style Multi-Cloud Smart Supply Chain Control Tower that provides

near-real-time supply chain visibility, demand forecasting, disruption

detection, inventory optimization, and controlled automation.



\## Project Status



Phase 1 - Development Environment and Git Setup



\## Planned Architecture



\- AWS S3 - Canonical data lake

\- AWS Glue - ETL and data catalog

\- AWS Athena - Data querying

\- AWS EventBridge / Kafka - Event streaming

\- Amazon EKS - Microservices

\- Amazon SageMaker - Machine learning

\- Azure Synapse Analytics - Analytics

\- Power BI - Executive dashboards

\- Azure OpenAI - Incident summarization

\- Terraform - Infrastructure as Code

\- GitHub Actions - CI/CD

\- Argo CD - GitOps



\## Data Sources



\- M5 Forecasting

\- Favorita Store Sales Forecasting

\- Olist Brazilian E-Commerce Public Dataset



\## Project Modules



1\. Data Ingestion \& Connectors

2\. Event Bus \& Streaming

3\. ETL, Catalog \& Curated Lake

4\. Feature Store

5\. Demand Forecasting

6\. Disruption Detection

7\. Optimization Engine

8\. Automation \& Orchestration

9\. NLP / Language Services
10\. Microservices \& API Gateway

11\. Dashboard / Frontend

12\. DevOps, CI/CD, Monitoring \& Governance



## Module 2: Real-Time Supply Chain Visibility with Apache Kafka

### Overview

This module implements a local event-driven pipeline for processing simulated shipment events. Apache Kafka transports shipment events from a Python producer to a Python consumer, which calculates supply-chain visibility KPIs.

### Architecture

```text
Python Shipment Event Producer
              |
              v
     Kafka: shipment-events
       (3 partitions)
              |
              v
     Python Kafka Consumer
              |
              v
       KPI Processing
       - ETA variance
       - Delay classification
       - Days of supply
       - Stockout risk
```

### Technology Stack

- Python
- Apache Kafka 4.1.0 (Docker image)
- Docker Desktop and Docker Compose
- `kafka-python` 3.0.11
- `pytest`

### Components

- `realtime/events.py` — defines the shipment event structure.
- `realtime/producer.py` — generates sample shipment events, serializes them to JSON, and publishes them to Kafka.
- `realtime/consumer.py` — consumes JSON events from Kafka and calculates visibility KPIs.
- `realtime/kpi.py` — contains ETA variance, delay classification, days-of-supply, and stockout-risk calculations.
- `tests/test_realtime_kpi.py` — tests the KPI calculation logic.
- `docker-compose.yml` — configures the local Kafka broker.

### Setup and Execution

**1. Start Kafka**

Ensure Docker Desktop is running, then execute from the repository root:

```powershell
docker compose up -d
```

**2. Create the shipment topic**

```powershell
docker exec smart-chain-kafka /opt/kafka/bin/kafka-topics.sh --create --topic shipment-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

If the topic already exists, it does not need to be created again.

**3. Install the Python dependencies**

```powershell
python -m pip install kafka-python pytest
```

**4. Start the consumer**

In one terminal:

```powershell
python .\realtime\consumer.py
```

**5. Publish shipment events**

In a second terminal:

```powershell
python .\realtime\producer.py
```

The consumer should display the incoming shipment events and their calculated KPIs.

### KPI Definitions

- **ETA variance:** difference between the current ETA and planned ETA, expressed in hours.
- **Delay status:** classifies a shipment as `ON_TIME`, `MINOR_DELAY`, `MODERATE_DELAY`, or `SEVERE_DELAY` according to the implemented thresholds.
- **Days of supply:** estimates how many days the available inventory can cover at the assumed daily demand.
- **Stockout risk:** classifies risk using days of supply relative to replenishment lead time.

### Testing

Run the existing KPI test suite:

```powershell
python -m pytest tests/test_realtime_kpi.py -v
```

Latest verification: **5 tests passed**. Python syntax checks also passed for the producer, consumer, and KPI modules.

### Current Scope and Limitations

- Shipment events are simulated locally; external carrier feeds are not yet integrated.
- Inventory, average daily demand, and lead time currently use demonstration values in the consumer.
- Kafka runs locally in Docker and uses a single broker with replication factor 1. This is a development setup, not a highly available production deployment.
- This module has not yet been deployed to AWS or integrated with Azure analytics.
- Demand forecasting, inventory optimization, and automated replenishment remain future integration steps.




