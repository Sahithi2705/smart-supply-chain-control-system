
from fastapi import FastAPI, HTTPException

try:
    from .storage import (
        get_all_shipments,
        get_shipment_by_id,
        get_shipment_kpis
    )
except ImportError:
    from storage import (
        get_all_shipments,
        get_shipment_by_id,
        get_shipment_kpis
    )


app = FastAPI(
    title="Smart Supply Chain - Module 2 API",
    description="API for real-time shipment events and operational KPIs",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "module": "Real-Time Supply Chain Event Processing"
    }


@app.get("/api/shipments")
def all_shipments(limit: int = 100):
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 1000"
        )

    records = get_all_shipments(limit)

    return {
        "total": len(records),
        "shipments": records
    }


@app.get("/api/shipments/kpis")
def shipment_kpis():
    return get_shipment_kpis()


@app.get("/api/shipments/{shipment_id}")
def shipment_by_id(shipment_id: str):
    records = get_shipment_by_id(shipment_id)

    if not records:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    return {
        "shipment_id": shipment_id,
        "total_events": len(records),
        "events": records
    }