"""
transform.py
The 'T' in ETL. Cleans raw_tickets.csv and produces a clean, analysis-ready dataset.

Steps:
1. Drop fully blank rows
2. Drop duplicate ticket_ids
3. Standardize category / priority / customer_segment (strip whitespace, title-case)
4. Parse inconsistent date formats into real datetimes
5. Fill missing agent as 'Unassigned'
6. Compute resolution_time_hours (for resolved tickets)
7. Flag SLA breach (business rule: Critical > 24h, High > 48h, Medium > 96h, Low > 168h)
"""
import pandas as pd
import numpy as np

RAW_PATH = "data/raw_tickets.csv"
CLEAN_PATH = "data/clean_tickets.csv"

SLA_HOURS = {"Critical": 24, "High": 48, "Medium": 96, "Low": 168}


def parse_mixed_date(value):
    """Try multiple known date formats used in this messy export."""
    if pd.isna(value):
        return pd.NaT
    for fmt in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%m-%d-%Y %H:%M"):
        try:
            return pd.to_datetime(value, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT  # unparseable -> null, handled downstream


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Drop rows that are entirely blank (corrupt export rows)
    df = df.dropna(how="all")

    # 2. Drop duplicate tickets (keep first occurrence)
    before = len(df)
    df = df.drop_duplicates(subset="ticket_id", keep="first")
    print(f"Dropped {before - len(df)} duplicate ticket rows")

    # 3. Standardize text fields (done step by step, not chained, so it's easy to follow)
    for col in ["category", "priority", "customer_segment", "status"]:
        df[col] = df[col].astype(str)          # make sure it's plain text
        df[col] = df[col].str.strip()           # remove extra spaces
        df[col] = df[col].str.title()           # "billing" / "BILLING" -> "Billing"
        df[col] = df[col].replace("Nan", np.nan)  # fix the "Nan" string side-effect from astype(str)

    # 4. Parse dates
    df["created_date"] = df["created_date"].apply(parse_mixed_date)
    df["resolved_date"] = df["resolved_date"].apply(parse_mixed_date)

    # drop rows where created_date failed to parse or is missing (can't analyze without it)
    before = len(df)
    df = df.dropna(subset=["created_date"])
    print(f"Dropped {before - len(df)} rows with unparseable/missing created_date")

    # 5. Fill missing agent
    df["agent"] = df["agent"].fillna("Unassigned")

    # 6. Resolution time in hours (NaN if still open)
    df["resolution_time_hours"] = (
        (df["resolved_date"] - df["created_date"]).dt.total_seconds() / 3600
    ).round(2)

    # 7. SLA breach flag
    def sla_breach(row):
        if pd.isna(row["resolution_time_hours"]):
            return "Open"  # not yet resolved
        limit = SLA_HOURS.get(row["priority"], 168)
        return "Breached" if row["resolution_time_hours"] > limit else "Within SLA"

    df["sla_status"] = df.apply(sla_breach, axis=1)

    # helpful derived time field for trend analysis
    df["created_month"] = df["created_date"].dt.to_period("M").astype(str)

    return df.reset_index(drop=True)


if __name__ == "__main__":
    raw = pd.read_csv(RAW_PATH)
    print(f"Loaded {len(raw)} raw rows")

    clean_df = clean(raw)
    clean_df.to_csv(CLEAN_PATH, index=False)

    print(f"\nSaved {len(clean_df)} clean rows -> {CLEAN_PATH}")
    print("\nSLA status breakdown:")
    print(clean_df["sla_status"].value_counts())