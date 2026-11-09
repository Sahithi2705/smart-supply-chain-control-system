
import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "shipment_events.db"
)


def initialize_database():
    """Create the database and safely upgrade its schema."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS shipment_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                shipment_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                warehouse_id TEXT NOT NULL,
                carrier_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                planned_eta TEXT NOT NULL,
                current_eta TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                eta_variance_hours REAL NOT NULL,
                delay_status TEXT NOT NULL,
                available_inventory INTEGER NOT NULL,
                average_daily_demand REAL NOT NULL,
                days_of_supply REAL NOT NULL,
                stockout_risk TEXT NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(shipment_events)"
            )
        }

        if "event_id" not in columns:
            connection.execute(
                "ALTER TABLE shipment_events ADD COLUMN event_id TEXT"
            )
        if "duplicate_of_id" not in columns:
            connection.execute(
                "ALTER TABLE shipment_events ADD COLUMN duplicate_of_id INTEGER"
    )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_shipment_events_event_id
            ON shipment_events(event_id)
            WHERE event_id IS NOT NULL
            """
        )



def save_shipment_event(event_data, kpis):
    """Save a shipment event once per unique event ID."""

    # Every event must have a valid, non-empty ID.
    event_id = event_data.get("event_id")

    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError(
            "Cannot save shipment event: event_id is missing or invalid."
        )

    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO shipment_events (
                event_id, shipment_id, order_id, sku, warehouse_id,
                carrier_id, event_type, planned_eta, current_eta,
                event_timestamp, eta_variance_hours, delay_status,
                available_inventory, average_daily_demand,
                days_of_supply, stockout_risk
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id.strip(),
                event_data["shipment_id"],
                event_data["order_id"],
                event_data["sku"],
                event_data["warehouse_id"],
                event_data["carrier_id"],
                event_data["event_type"],
                event_data["planned_eta"],
                event_data["current_eta"],
                event_data["timestamp"],
                kpis["eta_variance_hours"],
                kpis["delay_status"],
                kpis["available_inventory"],
                kpis["average_daily_demand"],
                kpis["days_of_supply"],
                kpis["stockout_risk"],
            ),
        )

        return cursor.rowcount == 1




def get_all_shipments(limit=100):
    """Retrieve the most recent processed shipment events."""
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT *
            FROM shipment_events
            ORDER BY event_timestamp DESC, id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        return [dict(row) for row in rows]


def get_shipment_by_id(shipment_id):
    """Retrieve all event records belonging to a shipment."""
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT *
            FROM shipment_events
            WHERE shipment_id = ?
            ORDER BY event_timestamp DESC, id DESC
            """,
            (shipment_id,)
        ).fetchall()

        return [dict(row) for row in rows]



def get_shipment_kpis():
    """Return event-level and latest-shipment-level KPIs."""

    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:

        # Exclude legacy records marked as duplicate candidates.
        event_row = connection.execute("""
            SELECT
                COUNT(*),
                SUM(CASE WHEN delay_status != 'ON_TIME'
                    THEN 1 ELSE 0 END),
                SUM(CASE WHEN stockout_risk = 'HIGH'
                    THEN 1 ELSE 0 END)
            FROM shipment_events
            WHERE duplicate_of_id IS NULL
        """).fetchone()
                # Count retained legacy duplicate records.
        duplicate_row = connection.execute("""
            SELECT COUNT(*)
            FROM shipment_events
            WHERE duplicate_of_id IS NOT NULL
        """).fetchone()

        # Select the latest event using event_timestamp.
        latest_rows = connection.execute("""
            SELECT
                current.shipment_id,
                current.delay_status,
                current.stockout_risk,
                current.eta_variance_hours
            FROM shipment_events AS current
            WHERE current.duplicate_of_id IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM shipment_events AS newer
                  WHERE newer.shipment_id = current.shipment_id
                    AND newer.duplicate_of_id IS NULL
                    AND (
                        newer.event_timestamp > current.event_timestamp
                        OR (
                            newer.event_timestamp = current.event_timestamp
                            AND newer.id > current.id
                        )
                    )
              )
        """).fetchall()

        total_shipments = len(latest_rows)

        delayed_shipments = sum(
            1 for row in latest_rows
            if row[1] != "ON_TIME"
        )

        high_risk_shipments = sum(
            1 for row in latest_rows
            if row[2] == "HIGH"
        )

        variances = [
            row[3] for row in latest_rows
            if row[3] is not None
        ]

        avg_variance = (
            sum(variances) / len(variances)
            if variances else None
        )

        return {
            "total_events": event_row[0],
            "delayed_events": event_row[1] or 0,
            "high_risk_events": event_row[2] or 0,
            "legacy_duplicate_records": duplicate_row[0],
            "unique_shipments": total_shipments,
            "delayed_shipments": delayed_shipments,
            "high_risk_shipments": high_risk_shipments,
            "avg_eta_variance": avg_variance
        }
