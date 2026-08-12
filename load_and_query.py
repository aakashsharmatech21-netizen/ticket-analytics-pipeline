"""
load_and_query.py
The 'L' in ETL + the SQL analytics layer.
Loads clean_tickets.csv into SQLite, then runs real analytical SQL
(joins not needed here since it's one table, but aggregations + window functions are).
Exports query results as CSVs for Power BI to consume.
"""
import sqlite3
import pandas as pd

DB_PATH = "data/tickets.db"
CLEAN_PATH = "data/clean_tickets.csv"


def load():
    df = pd.read_csv(CLEAN_PATH, parse_dates=["created_date", "resolved_date"])
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("tickets", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Loaded {len(df)} rows into {DB_PATH} (table: tickets)")


QUERIES = {
    # tickets by category + priority
    "tickets_by_category_priority": """
        SELECT category, priority, COUNT(*) AS ticket_count
        FROM tickets
        GROUP BY category, priority
        ORDER BY ticket_count DESC;
    """,

    # avg resolution time by agent (resolved tickets only)
    "avg_resolution_by_agent": """
        SELECT agent,
               COUNT(*) AS resolved_tickets,
               ROUND(AVG(resolution_time_hours), 1) AS avg_resolution_hours
        FROM tickets
        WHERE resolution_time_hours IS NOT NULL
        GROUP BY agent
        ORDER BY avg_resolution_hours ASC;
    """,

    # SLA breach rate by customer segment
    "sla_breach_by_segment": """
        SELECT customer_segment,
               SUM(CASE WHEN sla_status = 'Breached' THEN 1 ELSE 0 END) AS breached,
               COUNT(*) AS total_tickets,
               ROUND(100.0 * SUM(CASE WHEN sla_status = 'Breached' THEN 1 ELSE 0 END) / COUNT(*), 1) AS breach_pct
        FROM tickets
        GROUP BY customer_segment
        ORDER BY breach_pct DESC;
    """,

    # month-over-month ticket volume trend, using a window function
    "monthly_trend": """
        SELECT created_month,
               COUNT(*) AS ticket_count,
               LAG(COUNT(*)) OVER (ORDER BY created_month) AS prev_month_count,
               ROUND(100.0 * (COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY created_month))
                     / LAG(COUNT(*)) OVER (ORDER BY created_month), 1) AS mom_growth_pct
        FROM tickets
        GROUP BY created_month
        ORDER BY created_month;
    """,

    # top breach-prone categories
    "breach_by_category": """
        SELECT category,
               ROUND(100.0 * SUM(CASE WHEN sla_status = 'Breached' THEN 1 ELSE 0 END) / COUNT(*), 1) AS breach_pct,
               COUNT(*) AS total_tickets
        FROM tickets
        GROUP BY category
        ORDER BY breach_pct DESC;
    """,
}


def run_queries():
    conn = sqlite3.connect(DB_PATH)
    for name, sql in QUERIES.items():
        result = pd.read_sql_query(sql, conn)
        out_path = f"data/{name}.csv"
        result.to_csv(out_path, index=False)
        print(f"\n--- {name} ---")
        print(result.to_string(index=False))
        print(f"(saved -> {out_path})")
    conn.close()


if __name__ == "__main__":
    load()
    run_queries()
