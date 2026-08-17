"""
Generates a traceability report as a JSON file, summarising which
requirements were verified by which tests, with results. Designed
to be run in CI so every pipeline run produces durable evidence,
not just a pass/fail tick.
"""

import json
from datetime import datetime

from traceability_engine import TraceabilityEngine


def generate_report(output_path="traceability-report.json"):
    engine = TraceabilityEngine()
    matrix = engine.run_all()
    summary = engine.summary()
    orphans = engine.get_orphans()

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "orphans": orphans,
        "requirements": matrix,
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Traceability report written to {output_path}")
    print(f"Summary: {summary}")

    return report


if __name__ == "__main__":
    generate_report()
