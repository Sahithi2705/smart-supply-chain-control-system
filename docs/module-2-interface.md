# Module 2 — Real-Time Supply Chain Event Processing
## Integration Interface Specification

Version: 1.0.0
Status: Verified local implementation
Branch: feature/module-2-verified

## 1. Purpose

Module 2 consumes shipment events from Kafka, calculates shipment delay and
demonstration inventory-risk KPIs, persists events in SQLite, and exposes
shipment information through FastAPI.

The Streamlit dashboard consumes the API to display shipment status,
event history, delay analysis, and inventory risk.

## 2. Architecture

Kafka Producer
    |
    v
Kafka Topic: shipment-events
    |
    v
Kafka Consumer
    |
    +--> ETA variance and delay calculation
    |
    +--> Days-of-supply and stockout-risk calculation
    |
    v
SQLite: data/shipment_events.db
    |
    v
FastAPI
    |
    +--> Health endpoint
    +--> Shipment events endpoint
    +--> Shipment KPI endpoint
    +--> Shipment history endpoint
    |
    v
Streamlit Control Tower Dashboard

## 3. Kafka Event Contract

Topic: shipment-events
Bootstrap server: localhost:9092
Serialization: JSON

Expected event fields:

| Field | Description |
|---|---|
| event_id | Unique event identifier (UUID) |
| shipment_id | Shipment identifier |
| order_id | Associated order identifier |
| sku | Product identifier |
| warehouse_id | Warehouse identifier |
| carrier_id | Carrier identifier |
| event_type | Shipment event type |
| planned_eta | Planned estimated arrival time |
| current_eta | Current estimated arrival time |
| timestamp | Event occurrence timestamp |

Datetime fields use ISO 8601 string representations.

Demonstrated event types include SHIPMENT_DELAY and IN_TRANSIT.

Consumers should use event_id for duplicate detection and timestamp for
event-time ordering.

## 4. FastAPI Interface

Base URL: http://127.0.0.1:8000

### 4.1 Health

GET /health

Returns service health and module identification.

### 4.2 Retrieve shipment events

GET /api/shipments?limit=100

The limit must be between 1 and 1000.

Response structure:

{
  "total": 2,
  "shipments": [
    {
      "event_id": "example-uuid",
      "shipment_id": "SHP1001",
      "event_type": "SHIPMENT_DELAY"
    }
  ]
}

The example is illustrative; actual responses contain the stored event fields.

### 4.3 Retrieve shipment KPIs

GET /api/shipments/kpis

Response fields:

- total_events
- delayed_events
- high_risk_events
- legacy_duplicate_records
- unique_shipments
- delayed_shipments
- high_risk_shipments
- avg_eta_variance

### 4.4 Retrieve shipment history

GET /api/shipments/{shipment_id}

Returns shipment_id, total_events, and events.

Returns HTTP 404 when the shipment does not exist.

## 5. KPI Definitions

### ETA variance

ETA variance is calculated in hours from planned ETA and current ETA.

### Delay status

| ETA variance | Status |
|---|---|
| Less than or equal to 0 hours | ON_TIME |
| Greater than 0 and up to 4 hours | MINOR_DELAY |
| Greater than 4 and up to 8 hours | MODERATE_DELAY |
| Greater than 8 hours | SEVERE_DELAY |

### Days of supply

Days of supply = Available inventory / Average daily demand.

For zero or negative demand, the implementation returns infinity.

### Stockout risk

| Condition | Risk |
|---|---|
| Days of supply <= lead time | HIGH |
| Days of supply <= lead time + 3 | MEDIUM |
| Otherwise | LOW |

Current demonstration inputs:

- Available inventory: 120
- Average daily demand: 30
- Lead time: 5 days
- Calculated days of supply: 4 days
- Resulting stockout risk: HIGH

These values are simulated demonstration inputs, not live inventory data.

## 6. SQLite Storage Contract

Database file: data/shipment_events.db

Table: shipment_events

Important fields:

- id
- event_id
- shipment_id
- order_id
- sku
- warehouse_id
- carrier_id
- event_type
- planned_eta
- current_eta
- event_timestamp
- eta_variance_hours
- delay_status
- available_inventory
- average_daily_demand
- days_of_supply
- stockout_risk
- recorded_at
- duplicate_of_id

The database uses a unique partial index on non-null event_id values.

Events with missing or invalid event IDs are rejected.

Duplicate event IDs are ignored during insertion.

Existing legacy records are retained. Records marked with duplicate_of_id
are excluded from analytical KPI calculations.

Latest shipment state is determined using event_timestamp, with database
record ID as a tie-breaker. Older events are retained in shipment history.

## 7. Integration Guidance for Other Modules

### Module 3 — Demand Forecasting and Inventory Prediction

Module 3 may provide forecasted demand and inventory-related predictions.

The current Module 2 inventory and demand values are simulated. They must
not be treated as actual Module 3 forecasts.

A future integration should exchange SKU, warehouse, forecast horizon,
predicted demand, and prediction timestamp using an agreed mapping.

### Module 4 — Supply Chain Anomaly and Fraud Detection

Module 4 may analyse shipment events and provide anomaly or fraud alerts.

Use shipment identifiers, event identifiers, timestamps, and agreed
source mappings when correlating records.

Module 2 does not independently classify fraud.

### Module 5 — Risk Correlation and Decision Intelligence

Module 5 should combine relevant outputs from:

- Module 2: shipment events, delays, and shipment KPIs.
- Module 3: demand and inventory predictions.
- Module 4: anomaly and fraud alerts.

Module 5 should calculate its own combined risk score, incident priority,
and recommended actions.

Do not assume that identifiers from different source datasets are
interchangeable without an explicit mapping.

### Module 6 — Control Tower Visualisation and Workflow

Module 6 can consume Module 2 API endpoints to display shipment status,
event history, and operational KPIs.

Module 6 should use Module 5 outputs for consolidated risk prioritisation
rather than independently recalculating the cross-module risk score.

## 8. Current Limitations

- Kafka currently uses a single local broker.
- Topic replication factor is 1.
- No Kafka schema registry or formal schema version negotiation.
- No event-time watermark or explicit late-event rejection mechanism.
- Valid late events are retained; latest state is selected by timestamp.
- API currently has no authentication layer.
- Inventory and demand inputs are simulated.
- No live carrier tracking integration.
- No live ERP or warehouse inventory integration.
- The dashboard depends on the local FastAPI service.

## 9. Local Execution

Start Kafka:

docker start smart-chain-kafka

Start the consumer:

python -m realtime.consumer

Publish sample events:

python -m realtime.producer

Start the API:

python -m uvicorn realtime.api:app --host 127.0.0.1 --port 8000 --reload

API documentation:

http://127.0.0.1:8000/docs

Start the dashboard in another terminal:

python -m streamlit run dashboard/app.py

Dashboard:

http://localhost:8501

## 10. Verification Record

Previously verified locally:

- Kafka broker and shipment-events topic.
- Producer publishing and consumer processing.
- ETA variance and delay status calculation.
- Demonstration inventory-risk calculation.
- SQLite event persistence.
- Duplicate event protection.
- Invalid event ID rejection.
- Out-of-order event retention and timestamp-based latest-state selection.
- FastAPI endpoints.
- Streamlit dashboard display.
- Python compileall check.
- Existing automated test suite: 11 passed.

The automated test suite covers canonical sales and KPI tests. It does not
represent full automated end-to-end coverage of the entire Module 2 pipeline.
