"""Build the standalone executive dashboard: dashboard/dashboard.html (+ index.html).

Reads the KPI outputs (outputs/*.csv) and the SVG charts (images/*.svg) and
produces one self-contained HTML file — no server, no dependencies.
Run AFTER python/kpi_analysis.py.
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT, IMG = BASE / "outputs", BASE / "images"

def inr(n):
    s = str(int(round(float(n))))
    if len(s) <= 3: return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
    if head: parts.insert(0, head)
    return "₹" + ",".join(parts + [tail])

def inr_short(n):
    n = float(n)
    if abs(n) >= 1e7: return f"₹{n/1e7:.2f} Cr"
    if abs(n) >= 1e5: return f"₹{n/1e5:.1f} L"
    return inr(n)

def pct(v):
    return "—" if pd.isna(v) else f"{v:+.1f}%"

def svg_inline(path):
    txt = Path(path).read_text(encoding="utf-8")
    i = txt.find("<svg")
    return txt[i:] if i >= 0 else txt

s = pd.read_csv(OUT / "kpi_summary.csv").iloc[0]
ch = pd.read_csv(OUT / "sales_by_channel.csv")
cat = pd.read_csv(OUT / "sales_by_category.csv")
reg = pd.read_csv(OUT / "sales_by_region.csv")
seg = pd.read_csv(OUT / "customer_segments.csv")
prod = pd.read_csv(OUT / "top_products.csv")
monthly = pd.read_csv(OUT / "monthly_trend.csv", parse_dates=["Month"])
last = monthly.iloc[-1]
top_ch = ch.iloc[0]; top_cat = cat.iloc[0]
worst_ret = cat.loc[cat["Return Rate %"].idxmax()]
loyal = seg.loc[seg["Customer Segment"].str.startswith("Loyal")].iloc[0]

cards = [
    ("Total Revenue", inr_short(s["Total Revenue (INR)"]), inr(s["Total Revenue (INR)"])),
    ("Total Orders", f"{int(s['Total Orders']):,}", f"{int(s['Delivered Orders']):,} delivered"),
    ("Average Order Value", inr_short(s["Average Order Value (INR)"]), "per delivered order"),
    ("Gross Margin", f"{s['Gross Margin %']:.1f}%", "after product cost"),
    ("Return Rate", f"{s['Return Rate %']:.1f}%", f"cancellations {s['Cancellation Rate %']:.1f}%"),
    ("Repeat Customers", f"{s['Repeat Customer %']:.1f}%", f"{int(s['Active Customers']):,} active customers"),
]
cards_html = "".join(
    f'<div class="card"><div class="kpi-label">{a}</div><div class="kpi-value">{b}</div>'
    f'<div class="kpi-sub">{c}</div></div>' for a, b, c in cards)

def table(df, cols):
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for r in df.itertuples(index=False):
        d = dict(zip(df.columns, r))
        tds = ""
        for c in cols:
            v = d[c]
            if "Revenue (INR)" in c or "Order Value" in c: v = inr(v)
            elif isinstance(v, float) and ("%" in c or "Share" in c): v = f"{v:.1f}%"
            elif isinstance(v, float) and v == int(v): v = f"{int(v):,}"
            elif isinstance(v, (int,)): v = f"{v:,}"
            tds += f"<td>{v}</td>"
        body += f"<tr>{tds}</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"

growth_rows = "".join(
    f"<tr><td>{r.Month.strftime('%b %Y')}</td><td>{int(r.Orders):,}</td>"
    f"<td>{pct(r._5)}</td><td>{pct(r._7)}</td><td>{inr_short(r._3)}</td>"
    f"<td>{pct(r._8)}</td><td>{r._4:.1f}%</td></tr>"
    for r in monthly.tail(6).itertuples())
# (itertuples renames columns positionally; use explicit column order below instead)
growth_rows = ""
for _, r in monthly.tail(6).iterrows():
    growth_rows += (f"<tr><td>{r['Month'].strftime('%b %Y')}</td><td>{int(r['Orders']):,}</td>"
                    f"<td>{pct(r['Orders MoM Growth %'])}</td><td>{pct(r['Orders YoY Growth %'])}</td>"
                    f"<td>{inr_short(r['Revenue (INR)'])}</td>"
                    f"<td>{pct(r['Revenue (INR) YoY Growth %'])}</td>"
                    f"<td>{r['Return Rate %']:.1f}%</td></tr>")

charts = "".join(
    f'<div class="chart"><h3>{t}</h3>{svg_inline(IMG / f)}</div>'
    for f, t in [("revenue_by_category.svg", "Revenue by Product Category"),
                 ("revenue_by_channel.svg", "Revenue Share by Sales Channel"),
                 ("monthly_revenue_trend.svg", "Monthly Revenue Trend"),
                 ("yoy_growth_trend.svg", "Revenue — Year-over-Year Growth"),
                 ("top_products_revenue.svg", "Top Products by Revenue"),
                 ("return_rate_by_category.svg", "Return Rate by Product Category")])

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>E-Commerce Sales &amp; KPI Dashboard — Syed Musharaf</title>
<style>
* {{ box-sizing: border-box; margin: 0; font-family: 'Segoe UI', Arial, sans-serif; }}
body {{ background: #f2f5f8; color: #1c2733; }}
header {{ background: linear-gradient(120deg, #0d2b45, #1f6f8b); color: #fff; padding: 28px 36px; }}
header h1 {{ font-size: 26px; }} header p {{ opacity: .85; margin-top: 6px; font-size: 14px; }}
.badge {{ display: inline-block; background: #ffb703; color: #0d2b45; font-weight: 600;
  padding: 3px 12px; border-radius: 20px; font-size: 12px; margin-top: 12px; }}
main {{ max-width: 1180px; margin: 0 auto; padding: 24px 20px 40px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; }}
.card {{ background: #fff; border-radius: 12px; padding: 18px; box-shadow: 0 1px 4px rgba(13,43,69,.10); }}
.kpi-label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: #61707e; }}
.kpi-value {{ font-size: 27px; font-weight: 700; color: #0d2b45; margin: 6px 0 2px; }}
.kpi-sub {{ font-size: 12px; color: #61707e; }}
h2 {{ font-size: 18px; color: #0d2b45; margin: 28px 0 12px; }}
.panel {{ background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(13,43,69,.10); overflow-x: auto; }}
.insights {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
.insight {{ background: #fff7e8; border-left: 4px solid #ffb703; border-radius: 8px; padding: 14px 16px; font-size: 14px; line-height: 1.5; }}
.charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 14px; }}
.chart {{ background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 1px 4px rgba(13,43,69,.10); }}
.chart h3 {{ font-size: 14px; color: #0d2b45; margin-bottom: 8px; }}
.chart svg {{ width: 100%; height: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
th {{ text-align: left; padding: 9px 10px; background: #0d2b45; color: #fff; }}
td {{ padding: 8px 10px; border-bottom: 1px solid #e5ebf0; }}
tr:nth-child(even) td {{ background: #f7fafc; }}
footer {{ text-align: center; color: #61707e; font-size: 12.5px; padding: 22px; line-height: 1.6; }}
@media print {{ body {{ background: #fff; }} }}
</style></head><body>
<header>
  <h1>E-Commerce Sales &amp; KPI Dashboard</h1>
  <p>Executive Dashboard · Jan 2023 – Jun 2025 · Mobile App · Website · Marketplace · All values in INR (₹)</p>
  <span class="badge">Syed Musharaf · Data Analyst</span>
</header>
<main>
  <div class="grid">{cards_html}</div>

  <h2>Key Insights</h2>
  <div class="insights">
    <div class="insight"><strong>Mobile App is the #1 channel:</strong>
      {top_ch['Revenue Share %']:.1f}% of revenue ({inr_short(top_ch['Revenue (INR)'])}) —
      ahead of Website and Marketplace.</div>
    <div class="insight"><strong>{top_cat['Product Category']} drives the business:</strong>
      {inr_short(top_cat['Revenue (INR)'])} revenue, the largest category —
      but watch <strong>{worst_ret['Product Category']}</strong>: a {worst_ret['Return Rate %']:.1f}%
      return rate, the highest of any category.</div>
    <div class="insight"><strong>Loyal customers carry revenue:</strong>
      {int(loyal['Customers']):,} loyal buyers (5+ orders) generate
      {loyal['Revenue Share %']:.1f}% of all revenue, while one-time buyers are
      {100 * seg.iloc[0]['Customers'] / seg['Customers'].sum():.0f}% of customers but only
      {seg.iloc[0]['Revenue Share %']:.1f}% of revenue.</div>
    <div class="insight"><strong>Growth:</strong> latest month
      ({last['Month'].strftime('%b %Y')}) revenue is {pct(last['Revenue (INR) YoY Growth %'])}
      vs the same month last year (LAG year-over-year comparison).</div>
  </div>

  <h2>Sales by Channel</h2>
  <div class="panel">{table(ch, ["Sales Channel", "Orders", "Revenue (INR)", "Revenue Share %", "Average Order Value (INR)", "Return Rate %"])}</div>

  <h2>Sales by Category</h2>
  <div class="panel">{table(cat, ["Product Category", "Orders", "Units Sold", "Revenue (INR)", "Gross Margin %", "Return Rate %"])}</div>

  <h2>Sales by Region</h2>
  <div class="panel">{table(reg, ["Customer Region", "Orders", "Revenue (INR)", "Revenue Share %", "Average Order Value (INR)", "Return Rate %"])}</div>

  <h2>Customer Segments</h2>
  <div class="panel">{table(seg, ["Customer Segment", "Customers", "Orders", "Revenue (INR)", "Revenue Share %", "Average Order Value (INR)"])}</div>

  <h2>Growth — Monthly Comparison (LAG)</h2>
  <div class="panel"><table>
    <tr><th>Month</th><th>Orders</th><th>Orders MoM</th><th>Orders YoY</th>
        <th>Revenue</th><th>Revenue YoY</th><th>Return Rate</th></tr>
    {growth_rows}
  </table></div>

  <h2>Charts</h2>
  <div class="charts">{charts}</div>

  <h2>Top Products by Revenue</h2>
  <div class="panel">{table(prod.head(10), ["Product Name", "Product Category", "Units Sold", "Revenue (INR)", "Return Rate %"])}</div>
</main>
<footer>
  Built with PostgreSQL · Python (Pandas, SQLAlchemy) · Power BI (DAX) ·
  Dashboard generated by <code>dashboard/build_dashboard.py</code><br>
  Synthetic sample data (seed 42) modelled on a real e-commerce analytics
  project — no real company data.
</footer>
</body></html>"""

out = BASE / "dashboard" / "dashboard.html"
out.write_text(html, encoding="utf-8")
idx = BASE / "dashboard" / "index.html"
idx.write_text(html, encoding="utf-8")
print(f"dashboard written: {out} + index.html ({out.stat().st_size/1024:.0f} KB)")
