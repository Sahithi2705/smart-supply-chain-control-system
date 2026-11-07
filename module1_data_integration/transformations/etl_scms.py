
"""SCMS canonical procurement and delivery model."""

import pandas as pd

from config.settings import SCMS_FILE, CURATED
from transformations.common import (
    write_parquet,
    stable_key,
    assert_finite_numeric,
)

DATE_FIELDS = [
    "PQ First Sent to Client Date",
    "PO Sent to Vendor Date",
    "Scheduled Delivery Date",
    "Delivered to Client Date",
    "Delivery Recorded Date",
]

SHIPMENT_COLS = [
    "ASN/DN #",
    "PO / SO #",
    "Shipment Mode",
    "Fulfill Via",
    "Vendor INCO Term",
    "Country",
]

PRODUCT_COLS = [
    "Product Group",
    "Sub Classification",
    "Item Description",
    "Molecule/Test Type",
    "Brand",
    "Dosage",
    "Dosage Form",
    "Unit of Measure (Per Pack)",
]


def supplier_key_for(row):
    """Create a source-specific supplier business key."""
    return stable_key(
        row["Vendor"],
        row["Manufacturing Site"],
        row["Country"],
        row["Managed By"],
    )


def run_scms():

    if not SCMS_FILE.exists():
        raise FileNotFoundError(f"Missing SCMS source: {SCMS_FILE}")

    out = CURATED / "scms"
    out.mkdir(parents=True, exist_ok=True)

    src = pd.read_csv(
        SCMS_FILE,
        encoding="latin1",
        low_memory=False,
    )

    # Parse dates while preserving original source text.
    parsed = {}

    for col in DATE_FIELDS:
        parsed[col] = pd.to_datetime(
            src[col],
            errors="coerce",
            dayfirst=True,
            format="mixed",
        )

    # --------------------------------------------------
    # DIMENSION 1: SUPPLIER
    # --------------------------------------------------

    supplier = src[
        ["Vendor", "Manufacturing Site", "Managed By", "Country"]
    ].drop_duplicates().copy()

    supplier["supplier_key"] = supplier.apply(
        supplier_key_for,
        axis=1,
    )

    supplier = supplier.rename(columns={
        "Vendor": "vendor_name",
        "Manufacturing Site": "manufacturing_site",
        "Managed By": "managed_by",
        "Country": "country",
    })

    supplier["source_system"] = "SCMS"
    supplier["source_record_id"] = supplier["supplier_key"]

    write_parquet(
        supplier,
        out / "dim_supplier" / "part-00000.parquet",
    )

    # --------------------------------------------------
    # DIMENSION 2: SHIPMENT
    # --------------------------------------------------

    shipment = src[SHIPMENT_COLS].drop_duplicates().copy()

    shipment["shipment_key"] = shipment.apply(
        lambda r: stable_key(
            *[r[c] for c in SHIPMENT_COLS]
        ),
        axis=1,
    )

    shipment = shipment.rename(columns={
        "ASN/DN #": "asn_dn_number",
        "PO / SO #": "po_so_number",
        "Shipment Mode": "shipment_mode",
        "Fulfill Via": "fulfill_via",
        "Vendor INCO Term": "vendor_inco_term",
        "Country": "country",
    })

    shipment["source_system"] = "SCMS"
    shipment["source_record_id"] = shipment["shipment_key"]

    write_parquet(
        shipment,
        out / "dim_shipment" / "part-00000.parquet",
    )

    # --------------------------------------------------
    # DIMENSION 3: PRODUCT
    # --------------------------------------------------

    product = src[PRODUCT_COLS].drop_duplicates().copy()

    product["product_scms_key"] = product.apply(
        lambda r: stable_key(
            *[r[c] for c in PRODUCT_COLS]
        ),
        axis=1,
    )

    product = product.rename(columns={
        "Product Group": "product_group",
        "Sub Classification": "sub_classification",
        "Item Description": "item_description",
        "Molecule/Test Type": "molecule_test_type",
        "Brand": "brand",
        "Dosage": "dosage",
        "Dosage Form": "dosage_form",
        "Unit of Measure (Per Pack)": "unit_of_measure_per_pack",
    })

    product["source_system"] = "SCMS"
    product["source_record_id"] = product["product_scms_key"]

    write_parquet(
        product,
        out / "dim_product_scms" / "part-00000.parquet",
    )

    # --------------------------------------------------
    # WORKING DATA WITH DIMENSION KEYS
    # --------------------------------------------------

    work = src.copy()

    work["supplier_key"] = work.apply(
        supplier_key_for,
        axis=1,
    )

    work["shipment_key"] = work.apply(
        lambda r: stable_key(
            *[r[c] for c in SHIPMENT_COLS]
        ),
        axis=1,
    )

    work["product_scms_key"] = work.apply(
        lambda r: stable_key(
            *[r[c] for c in PRODUCT_COLS]
        ),
        axis=1,
    )

    work["source_system"] = "SCMS"
    work["source_record_id"] = work["ID"].astype("string")

    # --------------------------------------------------
    # FACT 1: PROCUREMENT
    # --------------------------------------------------

    procurement = work[[
        "ID",
        "Project Code",
        "PQ #",
        "PO / SO #",
        "supplier_key",
        "product_scms_key",
        "Line Item Quantity",
        "Unit of Measure (Per Pack)",
        "Line Item Value",
        "Pack Price",
        "Unit Price",
        "Country",
        "PQ First Sent to Client Date",
        "PO Sent to Vendor Date",
        "source_system",
        "source_record_id",
    ]].copy()

    procurement = procurement.rename(columns={
        "ID": "procurement_id",
        "Project Code": "project_code",
        "PQ #": "pq_number",
        "PO / SO #": "po_so_number",
        "Line Item Quantity": "line_item_quantity",
        "Unit of Measure (Per Pack)": "unit_of_measure_per_pack",
        "Line Item Value": "line_item_value_usd",
        "Pack Price": "pack_price_usd",
        "Unit Price": "unit_price_usd",
        "Country": "country",
        "PQ First Sent to Client Date": "pq_first_sent_to_client_date_source",
        "PO Sent to Vendor Date": "po_sent_to_vendor_date_source",
    })

    for col in [
        "line_item_quantity",
        "unit_of_measure_per_pack",
    ]:
        procurement[col] = pd.to_numeric(
            procurement[col],
            errors="coerce",
        ).astype("Int64")

    for col in [
        "line_item_value_usd",
        "pack_price_usd",
        "unit_price_usd",
    ]:
        procurement[col] = pd.to_numeric(
            procurement[col],
            errors="coerce",
        )

    assert_finite_numeric(
        procurement,
        [
            "line_item_value_usd",
            "pack_price_usd",
            "unit_price_usd",
        ],
        "SCMS.fact_procurement",
    )

    procurement["pq_first_sent_to_client_date"] = (
        parsed["PQ First Sent to Client Date"]
    )

    procurement["po_sent_to_vendor_date"] = (
        parsed["PO Sent to Vendor Date"]
    )

    write_parquet(
        procurement,
        out / "fact_procurement" / "part-00000.parquet",
    )

    # --------------------------------------------------
    # FACT 2: DELIVERY
    # --------------------------------------------------

    delivery = work[[
        "ID",
        "shipment_key",
        "supplier_key",
        "product_scms_key",
        "Shipment Mode",
        "Fulfill Via",
        "Scheduled Delivery Date",
        "Delivered to Client Date",
        "Delivery Recorded Date",
        "Line Item Quantity",
        "Weight (Kilograms)",
        "Freight Cost (USD)",
        "Line Item Insurance (USD)",
        "source_system",
        "source_record_id",
    ]].copy()

    delivery = delivery.rename(columns={
        "ID": "procurement_id",
        "Shipment Mode": "shipment_mode",
        "Fulfill Via": "fulfill_via",
        "Scheduled Delivery Date": "scheduled_delivery_date_source",
        "Delivered to Client Date": "delivered_to_client_date_source",
        "Delivery Recorded Date": "delivery_recorded_date_source",
        "Line Item Quantity": "line_item_quantity",
        "Weight (Kilograms)": "weight_kg",
        "Freight Cost (USD)": "freight_cost_usd",
        "Line Item Insurance (USD)": "line_item_insurance_usd",
    })

    # Keep datetime columns for accurate date arithmetic.
    delivery["scheduled_delivery_date"] = (
        parsed["Scheduled Delivery Date"]
    )

    delivery["delivered_to_client_date"] = (
        parsed["Delivered to Client Date"]
    )

    delivery["delivery_recorded_date"] = (
        parsed["Delivery Recorded Date"]
    )

    delivery["days_late_vs_schedule"] = (
        delivery["delivered_to_client_date"]
        - delivery["scheduled_delivery_date"]
    ).dt.days

    # Preserve original numeric values as source text.
    for col in [
        "weight_kg",
        "freight_cost_usd",
        "line_item_insurance_usd",
    ]:
        delivery[col + "_source"] = delivery[col].astype("string")

    delivery["line_item_quantity"] = pd.to_numeric(
        delivery["line_item_quantity"],
        errors="coerce",
    ).astype("Int64")

    for col in [
        "weight_kg",
        "freight_cost_usd",
        "line_item_insurance_usd",
    ]:
        delivery[col] = pd.to_numeric(
            delivery[col],
            errors="coerce",
        )

    assert_finite_numeric(
        delivery,
        [
            "weight_kg",
            "freight_cost_usd",
            "line_item_insurance_usd",
        ],
        "SCMS.fact_delivery",
    )

    write_parquet(
        delivery,
        out / "fact_delivery" / "part-00000.parquet",
    )

    # --------------------------------------------------
    # DATE QUALITY REPORT
    # --------------------------------------------------

    date_quality = []

    for col in DATE_FIELDS:
        date_quality.append({
            "source_column": col,
            "non_null_source_values": int(
                src[col].notna().sum()
            ),
            "parsed_dates": int(
                parsed[col].notna().sum()
            ),
            "unparsed_non_null_values": int(
                (
                    src[col].notna()
                    & parsed[col].isna()
                ).sum()
            ),
        })

    pd.DataFrame(date_quality).to_csv(
        out / "date_quality.csv",
        index=False,
    )

    print(
        f"SCMS canonical files written to {out}; "
        f"date quality: {date_quality}"
    )


if __name__ == "__main__":
    run_scms()
