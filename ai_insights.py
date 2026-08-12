"""
ai_insights.py
The AI differentiator layer. Takes the SQL-aggregated summary data (not raw tickets —
never send raw/PII-style data to an LLM) and generates a plain-English weekly ops
report, the same way a human analyst would summarize a dashboard for a manager.

Uses OpenRouter API - same pattern as your Support Ticket Classifier project.
Requires: OPENROUTER_API_KEY environment variable.
"""
import os
import json
import pandas as pd
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-4-26b-a4b-it:free"  # cheap/fast model, fine for summarization


def build_context() -> str:
    """Pulls the already-aggregated CSVs (not raw data) and turns them into a compact
    text summary to feed the LLM. Keeping input small = cheaper + more reliable output."""
    by_segment = pd.read_csv("data/sla_breach_by_segment.csv")
    by_category = pd.read_csv("data/breach_by_category.csv")
    trend = pd.read_csv("data/monthly_trend.csv").tail(3)
    by_agent = pd.read_csv("data/avg_resolution_by_agent.csv")

    context = f"""
SLA breach rate by customer segment:
{by_segment.to_string(index=False)}

SLA breach rate by ticket category:
{by_category.to_string(index=False)}

Recent 3-month ticket volume trend:
{trend.to_string(index=False)}

Average resolution time by agent (hours):
{by_agent.to_string(index=False)}
"""
    return context


def generate_report(context: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY environment variable before running this script."
        )

    system_prompt = (
        "You are a support-ops data analyst. You are given aggregated SQL query "
        "results from a support ticket database. Write a short, plain-English weekly "
        "report (max 200 words) for a non-technical manager: highlight the biggest "
        "risk area, one notable trend, and one concrete recommendation. No jargon, "
        "no repeating raw numbers unnecessarily — interpret them."
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
        "temperature": 0.4,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    ctx = build_context()
    print("Context sent to model:\n", ctx)

    try:
        report = generate_report(ctx)
        print("\n=== AI-Generated Weekly Ops Report ===\n")
        print(report)
        with open("data/weekly_ai_report.txt", "w") as f:
            f.write(report)
    except RuntimeError as e:
        print(f"\n[Skipped live call: {e}]")
        print("Run again with OPENROUTER_API_KEY set to generate the real report.")
