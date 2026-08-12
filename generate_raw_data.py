"""
generate_raw_data.py
Simulates a messy CSV export from a support ticketing system (like Zendesk/Freshdesk).
Intentionally includes nulls, duplicates, inconsistent casing/date formats —
mirrors what a real "Extract" step would receive.
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

N = 1200  # number of raw ticket rows

categories = ["Billing", "billing", "Technical", "technical ", "Account Access",
              "account access", "Feature Request", "Bug Report", "General Inquiry"]
priorities = ["Low", "Medium", "High", "Critical", "low", "high"]
segments = ["Enterprise", "SMB", "Individual", "enterprise", "smb"]
agents = ["Riya", "Karan", "Neha", "Vikram", "Sana", "Arjun", "Priya", "Amit"]
statuses = ["Resolved", "Closed", "Open", "Pending", "resolved"]

start_date = datetime(2026, 1, 1)

rows = []
for i in range(1, N + 1):
    created = start_date + timedelta(days=random.randint(0, 210), hours=random.randint(0, 23))

    # simulate resolution time (some tickets still open -> null resolved_date)
    is_resolved = random.random() > 0.12
    resolved = None
    if is_resolved:
        resolved = created + timedelta(hours=random.randint(1, 240))

    # inconsistent date formats to mimic real messy exports
    date_fmt = random.choice(["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%m-%d-%Y %H:%M"])
    created_str = created.strftime(date_fmt)
    resolved_str = resolved.strftime(date_fmt) if resolved else None

    row = {
        "ticket_id": f"TCK-{1000+i}",
        "category": random.choice(categories),
        "priority": random.choice(priorities),
        "customer_segment": random.choice(segments),
        "agent": random.choice(agents) if random.random() > 0.03 else None,  # some missing agent
        "status": random.choice(statuses),
        "created_date": created_str,
        "resolved_date": resolved_str,
    }
    rows.append(row)

df = pd.DataFrame(rows)

# inject duplicates (real exports often have re-synced rows)
dupes = df.sample(40, random_state=1)
df = pd.concat([df, dupes], ignore_index=True)

# inject a few fully blank/corrupt rows
for _ in range(8):
    df.loc[len(df)] = [None] * len(df.columns)

df = df.sample(frac=1, random_state=7).reset_index(drop=True)  # shuffle

df.to_csv("data/raw_tickets.csv", index=False)
print(f"Generated {len(df)} raw rows -> data/raw_tickets.csv")
print(df.head(8))
