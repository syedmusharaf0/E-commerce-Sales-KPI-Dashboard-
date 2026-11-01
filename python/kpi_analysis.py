"""KPI analysis: compute e-commerce KPIs with Pandas and export results + charts.

Mirrors sql/02_kpi_queries.sql. Revenue counts DELIVERED orders only
(returned and cancelled orders are analysed separately as rates).
Includes LAG-style growth: weekly (WoW), monthly (MoM + YoY), yearly (YoY).
Outputs -> outputs/ (CSV) and images/ (SVG charts). All values in INR.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT, IMG = BASE / "outputs", BASE / "images"
OUT.mkdir(exist_ok=True); IMG.mkdir(exist_ok=True)

dim = pd.read_csv(BASE / "data/dim_products.csv")
orders = pd.read_csv(BASE / "data/fact_orders.csv", parse_dates=["Order Date"])
orders["Order Cost (INR)"] = orders["Quantity"] * orders["Product Code"].map(
    dim.set_index("Product Code")["Unit Cost (INR)"])
orders = orders.merge(dim[["Product Code", "Product Name", "Product Category"]], on="Product Code")
_cust = pd.read_csv(BASE / "data/dim_customers.csv")[["Customer ID", "Customer City", "Customer Region"]]
orders = orders.merge(_cust, on="Customer ID")  # delivery city/region live in the customer dimension
dl = orders[orders["Order Status"] == "Delivered"]          # revenue-bearing orders
rt = orders[orders["Order Status"] == "Returned"]
cx = orders[orders["Order Status"] == "Cancelled"]
fulfilled = len(dl) + len(rt)

per_cust = dl.groupby("Customer ID").size()
repeat_pct = round(100 * (per_cust >= 2).mean(), 1)
summary = {
    "Total Revenue (INR)": round(dl["Order Value (INR)"].sum()),
    "Total Orders": len(orders),
    "Delivered Orders": len(dl),
    "Total Units Sold": int(dl["Quantity"].sum()),
    "Average Order Value (INR)": round(dl["Order Value (INR)"].mean()),
    "Gross Margin %": round(100 * (dl["Order Value (INR)"].sum() - dl["Order Cost (INR)"].sum())
                            / dl["Order Value (INR)"].sum(), 1),
    "Return Rate %": round(100 * len(rt) / fulfilled, 1),
    "Cancellation Rate %": round(100 * len(cx) / len(orders), 1),
    "Repeat Customer %": repeat_pct,
    "Active Customers": int(dl["Customer ID"].nunique()),
    "Average Discount %": round(dl["Discount %"].mean(), 1),
    "Average Delivery Days": round(dl["Delivery Days"].mean(), 1),
}
pd.DataFrame([summary]).to_csv(OUT / "kpi_summary.csv", index=False)

def rate_table(df_all: pd.DataFrame, df_dl: pd.DataFrame, key: str) -> pd.DataFrame:
    g = df_dl.groupby(key).agg(**{"Orders": ("Order ID", "count"),
                                  "Revenue (INR)": ("Order Value (INR)", "sum")}).reset_index()
    g["Revenue Share %"] = (100 * g["Revenue (INR)"] / g["Revenue (INR)"].sum()).round(1)
    g["Average Order Value (INR)"] = (g["Revenue (INR)"] / g["Orders"]).round(0)
    ret = df_all[df_all["Order Status"] == "Returned"].groupby(key)["Order ID"].count()
    ful = df_all[df_all["Order Status"] != "Cancelled"].groupby(key)["Order ID"].count()
    g["Return Rate %"] = g[key].map((100 * ret / ful).round(1))
    return g.sort_values("Revenue (INR)", ascending=False)

rate_table(orders, dl, "Sales Channel").to_csv(OUT / "sales_by_channel.csv", index=False)
rate_table(orders, dl, "Customer Region").to_csv(OUT / "sales_by_region.csv", index=False)

cat = dl.groupby("Product Category").agg(**{"Orders": ("Order ID", "count"),
                                            "Units Sold": ("Quantity", "sum"),
                                            "Revenue (INR)": ("Order Value (INR)", "sum"),
                                            "Cost (INR)": ("Order Cost (INR)", "sum")}).reset_index()
cat["Gross Margin %"] = (100 * (cat["Revenue (INR)"] - cat["Cost (INR)"]) / cat["Revenue (INR)"]).round(1)
ret = orders[orders["Order Status"] == "Returned"].groupby("Product Category")["Order ID"].count()
ful = orders[orders["Order Status"] != "Cancelled"].groupby("Product Category")["Order ID"].count()
cat["Return Rate %"] = cat["Product Category"].map((100 * ret / ful).round(1))
cat.drop(columns=["Cost (INR)"]).sort_values("Revenue (INR)", ascending=False).to_csv(
    OUT / "sales_by_category.csv", index=False)

prod = dl.groupby(["Product Code", "Product Name", "Product Category"]).agg(
    **{"Units Sold": ("Quantity", "sum"), "Revenue (INR)": ("Order Value (INR)", "sum")}).reset_index()
pret = orders[orders["Order Status"] == "Returned"].groupby("Product Code")["Order ID"].count()
pful = orders[orders["Order Status"] != "Cancelled"].groupby("Product Code")["Order ID"].count()
prod["Return Rate %"] = prod["Product Code"].map((100 * pret / pful).round(1))
prod.sort_values("Revenue (INR)", ascending=False).head(15).to_csv(OUT / "top_products.csv", index=False)

seg_counts = per_cust.rename("delivered_orders").reset_index()
seg_counts["Customer Segment"] = pd.cut(seg_counts["delivered_orders"], [0, 1, 4, 10**9],
                                        labels=["One-time Buyer", "Repeat Buyer (2-4 orders)",
                                                "Loyal Buyer (5+ orders)"])
seg = dl.merge(seg_counts[["Customer ID", "Customer Segment"]], on="Customer ID")
seg_t = seg.groupby("Customer Segment", observed=True).agg(
    **{"Customers": ("Customer ID", "nunique"), "Orders": ("Order ID", "count"),
       "Revenue (INR)": ("Order Value (INR)", "sum")}).reset_index()
seg_t["Revenue Share %"] = (100 * seg_t["Revenue (INR)"] / seg_t["Revenue (INR)"].sum()).round(1)
seg_t["Average Order Value (INR)"] = (seg_t["Revenue (INR)"] / seg_t["Orders"]).round(0)
seg_t.to_csv(OUT / "customer_segments.csv", index=False)

# ---------- Growth with LAG (shift in Pandas) ----------
def add_growth(df, cols, lags):
    df = df.copy()
    for lag, label in lags.items():
        for c in cols:
            prev = df[c].shift(lag)
            df[f"{c} {label} Growth %"] = (100 * (df[c] - prev) / prev).round(2)
    return df

o = dl.set_index("Order Date")
weekly = o.groupby(pd.Grouper(freq="W")).agg(**{"Orders": ("Order ID", "count"),
                                                 "Revenue (INR)": ("Order Value (INR)", "sum")})
weekly = add_growth(weekly.reset_index().rename(columns={"Order Date": "Week Ending"}),
                    ["Revenue (INR)", "Orders"], {1: "WoW"})
weekly.to_csv(OUT / "weekly_trend.csv", index=False)

monthly = o.groupby(pd.Grouper(freq="M")).agg(**{"Orders": ("Order ID", "count"),
                                                 "Revenue (INR)": ("Order Value (INR)", "sum")})
mret = rt.set_index("Order Date").groupby(pd.Grouper(freq="M"))["Order ID"].count()
monthly["Return Rate %"] = (100 * mret / (monthly["Orders"] + mret)).round(2)
monthly = add_growth(monthly.reset_index().rename(columns={"Order Date": "Month"}),
                     ["Revenue (INR)", "Orders"], {1: "MoM", 12: "YoY"})
monthly.to_csv(OUT / "monthly_trend.csv", index=False)

yearly = dl.assign(Year=dl["Order Date"].dt.year).groupby("Year").agg(
    **{"Orders": ("Order ID", "count"), "Revenue (INR)": ("Order Value (INR)", "sum")}).reset_index()
yearly["Period Note"] = yearly["Year"].apply(lambda y: "Jan-Jun only (partial year)" if y == 2025 else "Full year")
yearly = add_growth(yearly, ["Revenue (INR)", "Orders"], {1: "YoY"})
yearly.to_csv(OUT / "yearly_summary.csv", index=False)

# ---------------- Charts ----------------
plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#cccccc"})
cat_s = pd.read_csv(OUT / "sales_by_category.csv").sort_values("Revenue (INR)")
fig, ax = plt.subplots(figsize=(7, 4)); ax.barh(cat_s["Product Category"], cat_s["Revenue (INR)"] / 1e7, color="#1f6f8b")
ax.set_xlabel("Revenue (₹ Cr)"); ax.set_title("Revenue by Product Category")
fig.tight_layout(); fig.savefig(IMG / "revenue_by_category.svg", format="svg"); plt.close(fig)

ch = pd.read_csv(OUT / "sales_by_channel.csv")
fig, ax = plt.subplots(figsize=(5.5, 4))
ax.pie(ch["Revenue (INR)"], labels=ch["Sales Channel"], autopct="%1.1f%%",
       colors=["#1f6f8b", "#ffb703", "#0d2b45"], wedgeprops=dict(width=0.45, edgecolor="white"))
ax.set_title("Revenue Share by Sales Channel")
fig.tight_layout(); fig.savefig(IMG / "revenue_by_channel.svg", format="svg"); plt.close(fig)

r18 = monthly.tail(18)
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(r18["Month"].dt.strftime("%b %y"), r18["Revenue (INR)"] / 1e7, marker="o", ms=3.5, color="#1f6f8b")
ax.set_ylabel("Revenue (₹ Cr)"); ax.set_title("Monthly Revenue Trend (last 18 months)")
plt.setp(ax.get_xticklabels(), rotation=45, ha="left", fontsize=8.5)
fig.tight_layout(); fig.savefig(IMG / "monthly_revenue_trend.svg", format="svg"); plt.close(fig)

r12 = monthly.tail(12)
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(r12["Month"].dt.strftime("%b %y"), r12["Revenue (INR) YoY Growth %"],
       color=["#2e7d32" if v >= 0 else "#c0392b" for v in r12["Revenue (INR) YoY Growth %"]])
ax.axhline(0, color="#888", lw=.8); ax.set_ylabel("YoY growth (%)")
ax.set_title("Revenue — Year-over-Year Growth by Month")
plt.setp(ax.get_xticklabels(), rotation=45, ha="left", fontsize=8.5)
fig.tight_layout(); fig.savefig(IMG / "yoy_growth_trend.svg", format="svg"); plt.close(fig)

tp = prod.nlargest(8, "Revenue (INR)").iloc[::-1]
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.barh(tp["Product Name"], tp["Revenue (INR)"] / 1e5, color="#e67e22")
ax.set_xlabel("Revenue (₹ lakh)"); ax.set_title("Top Products by Revenue")
fig.tight_layout(); fig.savefig(IMG / "top_products_revenue.svg", format="svg"); plt.close(fig)

rr = cat.sort_values("Return Rate %")
fig, ax = plt.subplots(figsize=(7, 4)); ax.barh(rr["Product Category"], rr["Return Rate %"], color="#c0392b")
ax.set_xlabel("Return rate (%)"); ax.set_title("Return Rate by Product Category")
fig.tight_layout(); fig.savefig(IMG / "return_rate_by_category.svg", format="svg"); plt.close(fig)

print("SUMMARY:", summary)
print("\nBY CHANNEL:\n", pd.read_csv(OUT / 'sales_by_channel.csv').to_string(index=False))
print("\nBY CATEGORY:\n", pd.read_csv(OUT / 'sales_by_category.csv').to_string(index=False))
print("\nSEGMENTS:\n", seg_t.to_string(index=False))
print("\nYEARLY:\n", yearly.to_string(index=False))
print("\nLATEST MONTH:", monthly.iloc[-1].to_dict())
