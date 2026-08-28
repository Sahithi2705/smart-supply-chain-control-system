import pandas as pd


DATA_PATH = "data/curated/canonical_sales_m5_sample.csv"


def load_data():
    return pd.read_csv(DATA_PATH)


def test_required_columns_exist():
    df = load_data()

    required_columns = [
        "sales_date",
        "sku",
        "store_id",
        "quantity_sold",
        "unit_price",
        "dept_id",
        "category_id",
        "state_id",
        "source_system",
        "source_record_id",
    ]

    for column in required_columns:
        assert column in df.columns


def test_required_fields_not_null():
    df = load_data()

    required_fields = [
        "sales_date",
        "sku",
        "store_id",
        "source_system",
        "source_record_id",
    ]

    for column in required_fields:
        assert df[column].notna().all()


def test_quantity_is_not_negative():
    df = load_data()

    assert (df["quantity_sold"] >= 0).all()


def test_positive_sales_have_price():
    df = load_data()

    positive_sales = df[df["quantity_sold"] > 0]

    assert positive_sales["unit_price"].notna().all()


def test_source_system_is_m5():
    df = load_data()

    assert df["source_system"].eq("M5").all()


def test_no_duplicate_sales_records():
    df = load_data()

    duplicate_count = df.duplicated(
        subset=["sales_date", "sku", "store_id"]
    ).sum()

    assert duplicate_count == 0