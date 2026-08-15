"""
Traceability Engine
----------------------
Loads requirements.json, runs the linked test function for each
requirement (from test_requirements.py), and records PASS/FAIL
with a timestamp. This is the core "bidirectional traceability"
logic — requirements point to tests, and results point back to
requirements.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import test_requirements


class TraceabilityEngine:
    def __init__(self, requirements_path="requirements.json"):
        self.requirements_path = requirements_path
        self.requirements = self._load_requirements()
        self.results = {}  # test_id -> {"status": ..., "timestamp": ..., "error": ...}

    def _load_requirements(self):
        with open(self.requirements_path, "r") as f:
            return json.load(f)

    def _run_single_test(self, test_id):
        """Run one test function by name, using a fresh tmp_path-like folder."""
        test_func = getattr(test_requirements, test_id, None)
        if test_func is None:
            return {"status": "MISSING", "error": f"No test function named {test_id}"}

        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                test_func(Path(tmp_dir))
                return {"status": "PASS", "error": None}
            except AssertionError as e:
                return {"status": "FAIL", "error": str(e) or "Assertion failed"}
            except Exception as e:
                return {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}

    def run_all(self):
        """Run every requirement's linked test and store the result."""
        now = datetime.now().isoformat(timespec="seconds")
        for req in self.requirements:
            test_id = req["test_id"]
            outcome = self._run_single_test(test_id)
            self.results[test_id] = {
                "status": outcome["status"],
                "error": outcome["error"],
                "last_run": now,
            }
        return self.get_matrix()

    def get_matrix(self):
        """Return the full traceability matrix: requirements joined with results."""
        matrix = []
        for req in self.requirements:
            result = self.results.get(
                req["test_id"],
                {
                    "status": "NOT RUN",
                    "error": None,
                    "last_run": None,
                },
            )
            matrix.append(
                {
                    "id": req["id"],
                    "description": req["description"],
                    "category": req["category"],
                    "test_id": req["test_id"],
                    "status": result["status"],
                    "error": result["error"],
                    "last_run": result["last_run"],
                }
            )
        return matrix

    def summary(self):
        """Return pass/fail counts across the current results."""
        matrix = self.get_matrix()
        counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "MISSING": 0, "NOT RUN": 0}
        for row in matrix:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        return counts
