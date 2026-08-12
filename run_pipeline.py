"""
run_pipeline.py
One-command automation of the full pipeline:
Extract (raw CSV) -> Transform (clean) -> Load (SQLite) -> SQL analytics -> AI report

This is the script that would run on a schedule (e.g. daily/weekly cron) in a real
support-ops setting, instead of someone manually re-running each step.
"""
import subprocess
import sys


def run_step(script_name: str):
    print(f"\n{'='*50}\nRunning {script_name}\n{'='*50}")
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        print(f"Pipeline stopped: {script_name} failed.")
        sys.exit(1)


if __name__ == "__main__":
    run_step("transform.py")
    run_step("load_and_query.py")
    run_step("ai_insights.py")
    print("\nPipeline complete. Outputs ready in /data for Power BI import.")
