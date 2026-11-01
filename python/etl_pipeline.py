"""ETL pipeline: load raw CSV extracts, validate, clean and load into a database.

In production this targets PostgreSQL (see sql/01_schema_postgresql.sql).
For a self-contained local run it loads into a SQLite database file using the
same table/column names. Source CSVs carry friendly display headers; the ETL
maps them to database column names (standard ETL practice).
All monetary values are in Indian Rupees (INR).
"""
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

BASE = Path(__file__).resolve().parent.parent
DATA, DBDIR = BASE / "data", BASE / "database"
DBDIR.mkdir(exist_ok=True)

PRODUCT_COLUMNS = {"Product Code": "product_code", "Product Name": "product_name",
                   "Product Category": "product_category", "Selling Price (INR)": "selling_price_inr",
                   "Unit Cost (INR)": "unit_cost_inr"}
CUSTOMER_COLUMNS = {"Customer ID": "customer_id", "Customer City": "customer_city",
                    "Customer Region": "customer_region", "Acquisition Channel": "acquisition_channel",
                    "Signup Date": "signup_date"}
ORDER_COLUMNS = {"Order ID": "order_id", "Order Date": "order_date", "Customer ID": "customer_id",
                 "Product Code": "product_code", "Sales Channel": "sales_channel",
                 "Quantity": "quantity", "Unit Price (INR)": "unit_price_inr",
                 "Discount %": "discount_percent", "Order Value (INR)": "order_value_inr",
                 "Payment Method": "payment_method", "Order Status": "order_status",
                 "Delivery Days": "delivery_days"}

def validate(df: pd.DataFrame, name: str, key_cols: list[str]) -> None:
    assert not df.duplicated(subset=key_cols).any(), f"{name}: duplicate keys on {key_cols}"
    assert df[key_cols].notna().all().all(), f"{name}: null values in key columns"
    print(f"  [OK] {name}: {len(df):,} rows, keys unique, no null keys")

def main() -> None:
    print("EXTRACT")
    dim = pd.read_csv(DATA / "dim_products.csv").rename(columns=PRODUCT_COLUMNS)
    cust = pd.read_csv(DATA / "dim_customers.csv", parse_dates=["Signup Date"]).rename(columns=CUSTOMER_COLUMNS)
    orders = pd.read_csv(DATA / "fact_orders.csv", parse_dates=["Order Date"]).rename(columns=ORDER_COLUMNS)

    print("VALIDATE")
    validate(dim, "dim_products", ["product_code"])
    validate(cust, "dim_customers", ["customer_id"])
    validate(orders, "fact_orders", ["order_id"])
    assert set(orders["order_status"]) <= {"Delivered", "Returned", "Cancelled"}
    assert set(orders["sales_channel"]) <= {"Mobile App", "Website", "Marketplace"}
    assert orders["product_code"].isin(dim["product_code"]).all(), "order references unknown product"
    assert orders["customer_id"].isin(cust["customer_id"]).all(), "order references unknown customer"
    assert (orders["order_value_inr"] > 0).all(), "non-positive order value"
    print("  [OK] business-rule checks passed")

    print("TRANSFORM")
    orders["order_cost_inr"] = orders["quantity"] * orders["product_code"].map(
        dim.set_index("product_code")["unit_cost_inr"])
    orders["is_delivered"] = orders["order_status"] == "Delivered"
    print(f"  enriched fact_orders with order_cost_inr; delivered share: {orders['is_delivered'].mean():.1%}")

    print("LOAD")
    engine = create_engine(f"sqlite:///{DBDIR / 'ecommerce.db'}")
    dim.to_sql("dim_products", engine, if_exists="replace", index=False)
    cust.to_sql("dim_customers", engine, if_exists="replace", index=False)
    orders.to_sql("fact_orders", engine, if_exists="replace", index=False)
    print(f"  loaded 3 tables into {DBDIR / 'ecommerce.db'}")
    print(f"  delivered revenue (INR): {orders.loc[orders['is_delivered'], 'order_value_inr'].sum():,.0f}")

if __name__ == "__main__":
    main()
