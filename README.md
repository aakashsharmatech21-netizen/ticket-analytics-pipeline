# Support Ticket Analytics Pipeline

An end-to-end data pipeline that ingests raw support ticket data, cleans and
transforms it, loads it into SQL for analysis, powers a Power BI dashboard,
and uses an LLM to generate a plain-English weekly ops report from the
aggregated metrics — a companion project to my [Support Ticket Classifier](#),
extending it from "classify one ticket" to "analyze the whole ticket stream."

## Architecture

```
raw_tickets.csv (messy export)
        │
        ▼
 transform.py  ──►  clean_tickets.csv
   (Pandas: dedup, date normalization,
    SLA breach logic, feature engineering)
        │
        ▼
load_and_query.py  ──►  tickets.db (SQLite)
   (loads clean data, runs 5 analytical
    SQL queries incl. window functions)
        │
        ├──► CSV exports  ──►  Power BI Dashboard
        │
        ▼
  ai_insights.py  ──►  weekly_ai_report.txt
   (OpenRouter API summarizes the SQL
    aggregates into a manager-readable report)
```

All stages are chained by `run_pipeline.py` — one command runs the full
Extract → Transform → Load → Analyze → AI-Summarize flow, the way it would
run on a scheduled job in production.

## Why this exists

Most sample ETL projects clean a CSV and stop. This one goes further:
real SQL analysis (including window functions for trend analysis), a
genuine business rule (SLA breach detection by priority tier), and an AI
layer that turns raw numbers into something a non-technical manager could
actually read — the same gap between "data" and "decision" that BI/data
analyst work is meant to close.

## Tech Stack
- **Python** — Pandas, NumPy for ETL
- **SQLite** — analytical SQL layer (aggregations, CASE logic, window functions)
- **Power BI** — dashboard visualization
- **OpenRouter API** (Claude) — AI-generated summary report

## Key SQL techniques used
- Multi-column `GROUP BY` aggregation
- Conditional aggregation (`CASE WHEN` inside `SUM`)
- Window function (`LAG()`) for month-over-month trend calculation
- Derived business logic (SLA breach thresholds per priority tier)

## How to run

```bash
pip install -r requirements.txt

# generate sample raw data (skip if you have your own source data)
python generate_raw_data.py

# run the full pipeline: clean -> load -> query -> AI report
export OPENROUTER_API_KEY=your_key_here
python run_pipeline.py
```

Outputs land in `/data`:
- `clean_tickets.csv` — cleaned dataset
- `tickets.db` — SQLite database
- `*_by_*.csv` — query result exports (feed these into Power BI)
- `weekly_ai_report.txt` — AI-generated summary

## Dashboard

Power BI dashboard built on the query outputs, showing:
- Ticket volume by category & priority
- SLA breach rate by customer segment and category
- Agent-wise average resolution time
- Month-over-month ticket volume trend

*(screenshot/link added after dashboard build)*

## Data note
Sample data in this repo is synthetically generated (`generate_raw_data.py`)
to simulate a realistic messy support-ticket export — including inconsistent
date formats, duplicate rows, and missing values — so the cleaning logic in
`transform.py` reflects real-world data quality issues rather than a
pre-cleaned toy dataset.
