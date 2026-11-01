"""Generate the SAMPLE dataset for the E-Commerce Sales & KPI Dashboard project.

IMPORTANT: synthetic sample data for demonstration and learning, modelled on
the structure of a real e-commerce analytics project (orders, customers,
products) for an Indian online retailer. All monetary values in Indian
Rupees (INR). Column names are the friendly display names used in the
dashboards (see data/data_dictionary.md).
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)

# ---------------- Products: code, name, category, selling price INR, cost INR, popularity weight ----------------
PRODUCTS = [
    ("SKU-101", "Wireless Earbuds Pro", "Electronics", 2999, 1850, 10),
    ("SKU-102", "Smart Watch Series 5", "Electronics", 7999, 4900, 7),
    ("SKU-103", "Bluetooth Speaker", "Electronics", 1999, 1150, 8),
    ("SKU-104", "USB-C Fast Charger", "Electronics", 899, 420, 9),
    ("SKU-105", "Laptop Stand Aluminium", "Electronics", 1499, 780, 4),
    ("SKU-106", "Air Fryer 5L", "Electronics", 6499, 3900, 6),
    ("SKU-201", "Cotton T-Shirt", "Apparel", 799, 320, 10),
    ("SKU-202", "Denim Jacket", "Apparel", 1999, 890, 6),
    ("SKU-203", "Running Shoes", "Apparel", 2499, 1150, 8),
    ("SKU-204", "Winter Jacket NorthPeak", "Apparel", 2999, 1450, 4),
    ("SKU-205", "Cotton Kurti", "Apparel", 1299, 520, 7),
    ("SKU-301", "Organic Basmati Rice 5kg", "FMCG", 649, 430, 9),
    ("SKU-302", "Cold-Pressed Olive Oil 1L", "FMCG", 899, 560, 5),
    ("SKU-303", "Protein Powder 1kg", "FMCG", 1499, 820, 7),
    ("SKU-304", "Vitamin D3 Supplements", "FMCG", 599, 260, 6),
    ("SKU-305", "Green Tea 500g", "FMCG", 449, 190, 6),
    ("SKU-401", "Ceramic Dinner Set 12pc", "Home & Living", 2199, 1150, 4),
    ("SKU-402", "LED Desk Lamp", "Home & Living", 1299, 640, 5),
    ("SKU-403", "Memory Foam Pillow", "Home & Living", 1099, 520, 6),
    ("SKU-404", "Water Purifier 8L", "Home & Living", 9999, 6100, 3),
    ("SKU-405", "Cotton Bedsheet Set", "Home & Living", 1499, 680, 6),
    ("SKU-501", "Car Vacuum Cleaner", "Automotive", 1899, 940, 3),
    ("SKU-502", "Car Battery 12V 70Ah", "Automotive", 6999, 4600, 2),
    ("SKU-503", "Tyre Inflator Portable", "Automotive", 1299, 610, 3),
    ("SKU-601", "Yoga Mat Pro 6mm", "Sports", 999, 420, 7),
    ("SKU-602", "Dumbbell Set 10kg", "Sports", 1799, 880, 5),
    ("SKU-603", "Cricket Bat English Willow", "Sports", 2999, 1550, 4),
    ("SKU-604", "Badminton Racket", "Sports", 1199, 540, 5),
    ("SKU-701", "Vitamin C Face Serum", "Beauty", 699, 240, 8),
    ("SKU-702", "Herbal Hair Oil 200ml", "Beauty", 349, 120, 7),
]
dim = pd.DataFrame(PRODUCTS, columns=["Product Code", "Product Name", "Product Category",
                                      "Selling Price (INR)", "Unit Cost (INR)", "Popularity Weight"])
dim.drop(columns=["Popularity Weight"]).to_csv(DATA / "dim_products.csv", index=False)
weights = (dim["Popularity Weight"] / dim["Popularity Weight"].sum()).to_numpy()

# ---------------- Customers ----------------
CITIES = [("Mumbai", "West", 14), ("Delhi", "North", 13), ("Bengaluru", "South", 13),
          ("Hyderabad", "South", 10), ("Chennai", "South", 9), ("Kolkata", "East", 8),
          ("Pune", "West", 8), ("Ahmedabad", "West", 6), ("Jaipur", "North", 6),
          ("Lucknow", "North", 5), ("Kochi", "South", 4), ("Guwahati", "East", 4)]
city_names = [c for c, _, _ in CITIES]
city_region = {c: r for c, r, _ in CITIES}
city_w = np.array([w for _, _, w in CITIES], dtype=float); city_w /= city_w.sum()
CHANNELS = ["Mobile App", "Website", "Marketplace"]
CH_W = [0.42, 0.38, 0.20]

N_CUST = 9000
cust_rows = []
for i in range(N_CUST):
    signup = pd.Timestamp("2021-06-01") + pd.Timedelta(days=int(rng.integers(0, 570)))
    cust_rows.append((f"CUST-{10001 + i}", rng.choice(city_names, p=city_w),
                      rng.choice(CHANNELS, p=CH_W), signup.date()))
customers = pd.DataFrame(cust_rows, columns=["Customer ID", "Customer City",
                                             "Acquisition Channel", "Signup Date"])
customers.insert(2, "Customer Region", customers["Customer City"].map(city_region))
customers.to_csv(DATA / "dim_customers.csv", index=False)
cust_by_city = customers.set_index("Customer ID")

# Realistic purchase-frequency mix: ~30% of customers buy once, a small loyal
# base buys often. Build a shuffled "slot" per expected order and hand slots
# out as orders are generated, so segments (one-time / repeat / loyal) emerge
# naturally instead of every customer buying equally often.
_brackets = [(1, 1), (2, 3), (4, 6), (7, 12), (13, 30)]
_pick = rng.choice(len(_brackets), size=N_CUST, p=[.30, .20, .20, .17, .13])
_counts = np.array([rng.integers(_brackets[k][0], _brackets[k][1] + 1) for k in _pick])
_counts = np.maximum(1, np.round(_counts * 1.15).astype(int))
slots = np.repeat(customers["Customer ID"].to_numpy(), _counts)
rng.shuffle(slots)
slot_i = 0

# ---------------- Orders: Jan 2023 - Jun 2025 ----------------
RETURN_RATE = {"Apparel": 0.14, "Electronics": 0.05, "FMCG": 0.02, "Home & Living": 0.07,
               "Automotive": 0.06, "Sports": 0.08, "Beauty": 0.04}
PAYMENTS = ["UPI", "Credit/Debit Card", "Cash on Delivery", "Net Banking"]
PAY_W = [0.46, 0.24, 0.22, 0.08]
prod_lookup = dim.set_index("Product Code")

dates = pd.date_range("2023-01-01", "2025-06-30", freq="D")
rows, oid = [], 500000
for d in dates:
    months_in = (d.year - 2023) * 12 + (d.month - 1)
    trend = 1.006 ** months_in                       # ~7% yearly growth
    weekly = 1.25 if d.weekday() >= 5 else 1.0       # weekend lift
    festival = 1.6 if (d.month == 10 and d.day >= 15) or (d.month == 11 and d.day <= 15) else 1.0  # Diwali season
    n_orders = int(rng.poisson(38 * trend * weekly * festival))
    for _ in range(n_orders):
        oid += 1
        code = rng.choice(dim["Product Code"], p=weights)
        p = prod_lookup.loc[code]
        cust_id = slots[slot_i % len(slots)]; slot_i += 1
        cust = cust_by_city.loc[cust_id]
        channel = rng.choice(CHANNELS, p=CH_W)
        qty = int(rng.choice([1, 1, 1, 2, 2, 3], p=[.55, .15, .05, .15, .05, .05]))
        base_disc = {"Mobile App": 8, "Website": 10, "Marketplace": 16}[channel]
        discount = float(np.clip(rng.normal(base_disc + (6 if festival > 1 else 0), 4), 0, 45))
        revenue = round(qty * p["Selling Price (INR)"] * (1 - discount / 100))
        r = rng.random()
        if r < 0.04: status = "Cancelled"
        elif r < 0.04 + RETURN_RATE[p["Product Category"]]: status = "Returned"
        else: status = "Delivered"
        rows.append((f"ORD-{oid}", d.date(), cust_id,
                     code, channel, qty, p["Selling Price (INR)"], round(discount, 1), revenue,
                     rng.choice(PAYMENTS, p=PAY_W), status, int(rng.integers(2, 8))))
orders = pd.DataFrame(rows, columns=["Order ID", "Order Date", "Customer ID",
                                     "Product Code", "Sales Channel",
                                     "Quantity", "Unit Price (INR)", "Discount %",
                                     "Order Value (INR)", "Payment Method", "Order Status",
                                     "Delivery Days"])
orders.to_csv(DATA / "fact_orders.csv", index=False)
delivered = orders[orders["Order Status"] == "Delivered"]
print(f"products: {len(dim)} | customers: {len(customers)} | orders: {len(orders)} "
      f"| delivered revenue: ₹{delivered['Order Value (INR)'].sum():,.0f}")
