# Power BI Dashboard — Professional Build Guide

Build the `.pbix` in **Power BI Desktop** (free from Microsoft) in about
20 minutes using this pack. Everything is specified exactly: data load,
model, measures, page layouts, colours and formatting.

## Pack contents
| File | Use |
|---|---|
| `power_query_m.txt` | Paste into Power BI to load the 3 tables with correct types |
| `dax_measures.dax` | All measures — create a measure table and paste them in |
| This guide | Page-by-page layout spec |

## Step 1 — Load the data (5 min)
1. **Get Data → Blank Query** → Advanced Editor → paste each block from
   `power_query_m.txt` (set your `DataFolder` path). Name the queries
   `dim_products`, `dim_customers`, `fact_orders`. **Close & Apply**.
2. **Model view:** relationships — `dim_products[Product Code]` →
   `fact_orders[Product Code]`; `dim_customers[Customer ID]` →
   `fact_orders[Customer ID]` (one-to-many, single direction).
3. **Modeling → New table:** paste the `Calendar` DAX from the end of
   `power_query_m.txt`; relate `Calendar[Date]` → `fact_orders[Order Date]`;
   right-click Calendar → **Mark as date table**.

## Step 2 — Create the measures (5 min)
Modeling → New table → name it `_Measures`. Paste each measure from
`dax_measures.dax`. Hide the raw numeric fact columns so builders use
measures only. **Formatting:** currency measures (Total Revenue INR,
Average Order Value INR) → `₹ #,##0`; percent measures → 0.0 with "%".

## Theme (View → Themes → Customize current theme)
| Role | Colour |
|---|---|
| Primary / headers | `#0D2B45` (deep navy) |
| Secondary / bars | `#1F6F8B` (teal) |
| Accent / highlights | `#FFB703` (amber) |
| Alert (returns, cancellations) | `#C0392B` |
| Page background | `#F2F5F8` |
Font: Segoe UI. Page size: 16:9.

## Step 3 — Build the pages (10 min)

### Page 1 — Executive Overview
- **KPI cards:** Total Revenue INR · Total Orders · Average Order Value INR ·
  Gross Margin % · Return Rate % · Repeat Customer %.
- **Donut:** Revenue Share by `Sales Channel`.
- **Bar chart:** Total Revenue INR by `Product Category` (teal, data labels).
- **Line chart:** monthly Total Revenue INR (last 18 months).
- **Slicers (top):** `Sales Channel`, `Product Category`, `Customer Region`, month.

### Page 2 — Growth & Trends (LAG comparisons)
- **Combo chart:** month axis; columns = Total Revenue INR; line = **Revenue YoY Growth %**.
- **Line chart:** **Revenue MoM Growth %** by month.
- **Weekly clustered column:** revenue by Calendar week with **Revenue WoW Growth %** line (secondary axis).
- **Table:** month, Delivered Orders, Orders YoY Growth %, Total Revenue INR,
  Revenue MoM Growth %, Revenue YoY Growth % — data bars + green/red on growth.
- Yearly small table with the note "2025: Jan–Jun only (partial year)".

### Page 3 — Category & Product Deep-Dive
- **Bar chart:** Gross Margin % by `Product Category`.
- **Bar chart (alert red):** Return Rate % by `Product Category` — Apparel leads.
- **Table — Top products:** Product Name, category, Total Units Sold,
  Total Revenue INR, Return Rate % (Top N filter = 15).
- **Matrix:** category × channel revenue with colour scale.
- Enable **drill-through** on Product Name from Page 1.

### Page 4 — Customers & Regions
- **Donut or bar:** revenue by customer segment — build segments from
  `outputs/customer_segments.csv` logic (One-time / Repeat 2–4 / Loyal 5+).
- **Bar chart:** Total Revenue INR by `Customer Region` (West / North / South / East).
- **Table:** top 15 cities by revenue (`Customer City`).
- **Cards:** Active Customers · Repeat Customer % · Average Discount %.

## Step 4 — Polish & publish
- Amber header band + white title text on each page.
- Every visual titled in plain words; ₹ values use `₹ #,##0`; no "Sum of …" titles.
- **File → Publish** (free Power BI account) or keep the `.pbix` and export
  page 1 as PNG/PDF for your portfolio and LinkedIn.

> The browser version of this same dashboard lives in `dashboard.html`
> (open in any browser); the README shows the composed dashboard image
> (`images/power_bi_dashboard.svg`). The Power BI version adds slicers,
> drill-through and live growth comparisons on the same data and measures.
