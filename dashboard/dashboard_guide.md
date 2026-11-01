# Dashboard Guide

Four ways to view this project's dashboards — same data, same KPIs:

1. **README dashboard image** — `images/power_bi_dashboard.svg`, one full
   dashboard (KPI cards + 6 panels) shown at the top of the README;
   regenerate with `python dashboard/build_dashboard_image.py`.

2. **Interactive HTML dashboard** — `dashboard/dashboard.html`
   Complete, self-contained executive dashboard (open in any browser, no
   licence needed). The folder also contains `index.html` (identical file),
   so it deploys as a static site: on **Vercel** set Root Directory =
   `dashboard` (Framework: Other, no build command).

3. **Power BI dashboard** — build the `.pbix` in Power BI Desktop using
   `dashboard/powerbi_build_guide.md` (page-by-page spec, theme, formatting),
   `dashboard/power_query_m.txt` (data load) and
   `dashboard/dax_measures.dax` (all measures incl. WoW / MoM / YoY growth).

4. **Result tables** — `outputs/*.csv` for the raw KPI numbers behind every
   visual, including weekly / monthly / yearly trends with LAG growth %.

## Refresh
Re-run `python/etl_pipeline.py`, then `python/kpi_analysis.py`, then
`python dashboard/build_dashboard.py` and
`python dashboard/build_dashboard_image.py` whenever the data changes.
In Power BI, one click on **Refresh** reloads the same CSVs.
