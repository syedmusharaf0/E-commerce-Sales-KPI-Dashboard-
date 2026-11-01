"""Build ONE full dashboard image (images/power_bi_dashboard.svg) for the README.

A complete Power BI-style dashboard composed as a single figure: header band,
KPI card row, and six chart panels — so the GitHub README opens with the full
dashboard, followed by the individual graphs and tables.
Run AFTER python/kpi_analysis.py. A PNG twin is written for preview.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT, IMG = BASE / "outputs", BASE / "images"
NAVY, TEAL, AMBER, RED, GREEN, GREY = "#0d2b45", "#1f6f8b", "#ffb703", "#c0392b", "#2e7d32", "#61707e"

s = pd.read_csv(OUT / "kpi_summary.csv").iloc[0]
ch = pd.read_csv(OUT / "sales_by_channel.csv")
cat = pd.read_csv(OUT / "sales_by_category.csv")
prod = pd.read_csv(OUT / "top_products.csv")
monthly = pd.read_csv(OUT / "monthly_trend.csv", parse_dates=["Month"])

def inr_short(n):
    n = float(n)
    if abs(n) >= 1e7: return f"₹{n/1e7:.2f} Cr"
    if abs(n) >= 1e5: return f"₹{n/1e5:.1f} L"
    return f"₹{n:,.0f}"

plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#d5dde3", "axes.linewidth": 0.8,
                     "text.color": "#1c2733", "axes.labelcolor": GREY, "xtick.color": GREY,
                     "ytick.color": GREY, "axes.titlesize": 13, "axes.titleweight": "bold",
                     "axes.titlecolor": NAVY})
fig = plt.figure(figsize=(16, 11.6))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(4, 3, height_ratios=[0.62, 0.85, 1.55, 1.55],
                      hspace=0.50, wspace=0.38, left=0.084, right=0.978, top=0.965, bottom=0.062)

axh = fig.add_subplot(gs[0, :]); axh.axis("off")
axh.add_patch(FancyBboxPatch((0, 0.18), 1, 0.78, boxstyle="round,pad=0.004,rounding_size=0.012",
                             transform=axh.transAxes, facecolor=NAVY, edgecolor="none"))
axh.text(0.018, 0.70, "E-Commerce Sales & KPI Dashboard — Power BI",
         transform=axh.transAxes, color="white", fontsize=19, fontweight="bold", va="center")
axh.text(0.018, 0.34, "Mobile App  ·  Website  ·  Marketplace     |     Jan 2023 – Jun 2025     |     All values in INR (₹)",
         transform=axh.transAxes, color="#cfe3ec", fontsize=12.5, va="center")
axh.text(0.982, 0.52, "Syed Musharaf · Data Analyst", transform=axh.transAxes,
         color=AMBER, fontsize=12.5, fontweight="bold", va="center", ha="right")

kpis = [("TOTAL REVENUE", inr_short(s["Total Revenue (INR)"]), "delivered orders"),
        ("TOTAL ORDERS", f"{int(s['Total Orders']):,}", f"{int(s['Delivered Orders']):,} delivered"),
        ("AVG ORDER VALUE", inr_short(s["Average Order Value (INR)"]), "per delivered order"),
        ("GROSS MARGIN", f"{s['Gross Margin %']:.1f}%", "after product cost"),
        ("RETURN RATE", f"{s['Return Rate %']:.1f}%", f"cancellations {s['Cancellation Rate %']:.1f}%"),
        ("REPEAT CUSTOMERS", f"{s['Repeat Customer %']:.1f}%", "ordered 2+ times"),
        ("UNITS SOLD", f"{int(s['Total Units Sold']):,}", f"{int(s['Active Customers']):,} customers")]
axk = fig.add_subplot(gs[1, :]); axk.axis("off"); axk.set_xlim(0, 7); axk.set_ylim(0, 1)
for i, (label, value, sub) in enumerate(kpis):
    axk.add_patch(FancyBboxPatch((i + 0.04, 0.10), 0.92, 0.84,
                                 boxstyle="round,pad=0.01,rounding_size=0.05",
                                 facecolor="#f2f7fa", edgecolor="#d5dde3", linewidth=1))
    axk.text(i + 0.5, 0.76, label, ha="center", fontsize=8.6, color=GREY, fontweight="bold")
    axk.text(i + 0.5, 0.47, value, ha="center", fontsize=15.5, color=NAVY, fontweight="bold")
    axk.text(i + 0.5, 0.22, sub, ha="center", fontsize=8.4, color=GREY)

def panel(ax, title):
    ax.set_title(title, loc="left", pad=10)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(axis="x", color="#eef2f5", linewidth=0.8); ax.set_axisbelow(True)

ax = fig.add_subplot(gs[2, 0]); panel(ax, "Revenue by Product Category")
c = cat.sort_values("Revenue (INR)")
ax.barh(c["Product Category"], c["Revenue (INR)"] / 1e7, color=TEAL)
ax.set_xlabel("Revenue (₹ Cr)"); ax.tick_params(labelsize=10)

ax = fig.add_subplot(gs[2, 1]); panel(ax, "Monthly Revenue Trend (last 18 months)")
r18 = monthly.tail(18)
ax.plot(r18["Month"].dt.strftime("%b %y"), r18["Revenue (INR)"] / 1e7, marker="o", ms=3.5, color=TEAL, lw=1.8)
ax.grid(axis="y", color="#eef2f5", linewidth=0.8)
plt.setp(ax.get_xticklabels(), rotation=45, ha="left", fontsize=8.5); ax.set_ylabel("Revenue (₹ Cr)")

ax = fig.add_subplot(gs[2, 2]); panel(ax, "Revenue — YoY Growth by Month")
r12 = monthly.tail(12)
ax.bar(r12["Month"].dt.strftime("%b %y"), r12["Revenue (INR) YoY Growth %"],
       color=[GREEN if v >= 0 else RED for v in r12["Revenue (INR) YoY Growth %"]])
ax.axhline(0, color="#9fb2bf", lw=0.9); ax.grid(axis="y", color="#eef2f5", linewidth=0.8)
plt.setp(ax.get_xticklabels(), rotation=45, ha="left", fontsize=8.5); ax.set_ylabel("YoY growth (%)")

ax = fig.add_subplot(gs[3, 0]); panel(ax, "Revenue Share by Sales Channel")
ax.pie(ch["Revenue (INR)"], labels=ch["Sales Channel"], autopct="%1.1f%%",
       colors=[TEAL, AMBER, RED], wedgeprops=dict(width=0.45, edgecolor="white"),
       textprops=dict(fontsize=10.5))
ax.grid(False)

ax = fig.add_subplot(gs[3, 1]); panel(ax, "Top Products by Revenue")
tp = prod.sort_values("Revenue (INR)").tail(6)
ax.barh(tp["Product Name"], tp["Revenue (INR)"] / 1e5, color="#e67e22")
ax.set_xlabel("Revenue (₹ lakh)"); ax.tick_params(labelsize=9.5)

ax = fig.add_subplot(gs[3, 2]); panel(ax, "Return Rate by Product Category")
rr = cat.sort_values("Return Rate %")
ax.barh(rr["Product Category"], rr["Return Rate %"], color=RED)
ax.set_xlabel("Return rate (%)"); ax.tick_params(labelsize=10)

fig.text(0.5, 0.008, "Built with PostgreSQL · Python (Pandas, SQLAlchemy) · Power BI (DAX)   |   Synthetic sample data (seed 42) for demonstration — no real company data",
         ha="center", fontsize=10, color=GREY)
fig.savefig(IMG / "power_bi_dashboard.svg", format="svg")
fig.savefig("/tmp/ecommerce_dashboard.png", format="png", dpi=110)
print("dashboard image written:", round((IMG / 'power_bi_dashboard.svg').stat().st_size / 1024), "KB (svg)")
