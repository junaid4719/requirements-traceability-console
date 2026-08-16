"""
Traceability Engine
----------------------
Loads requirements.json and tests.json, runs the linked test function
for each requirement (from test_requirements.py), and permanently
records every run as an evidence entry in a local SQLite database —
so history survives restarts, not just the current session.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import test_requirements
import database


class TraceabilityEngine:
    def __init__(
        self,
        requirements_path="requirements.json",
        tests_path="tests.json",
        db_path="traceability.db",
    ):
        self.requirements_path = requirements_path
        self.tests_path = tests_path
        self.db_path = db_path
        self.requirements = self._load_json(requirements_path)
        self.tests = self._load_json(tests_path)
        self.tests_by_id = {t["id"]: t for t in self.tests}
        database.init_db(self.db_path)

    def _load_json(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def _run_single_test(self, function_name):
        """Run one test function by name, using a fresh temp folder."""
        test_func = getattr(test_requirements, function_name, None)
        if test_func is None:
            return {
                "status": "MISSING",
                "error": f"No test function named {function_name}",
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                test_func(Path(tmp_dir))
                return {"status": "PASS", "error": None}
            except AssertionError as e:
                return {"status": "FAIL", "error": str(e) or "Assertion failed"}
            except Exception as e:
                return {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}

    def run_all(self):
        """Run every requirement's linked test and permanently record the result."""
        now = datetime.now().isoformat(timespec="seconds")
        for req in self.requirements:
            test_ref = req.get("test_ref")
            test_def = self.tests_by_id.get(test_ref)

            if test_def is None:
                outcome = {
                    "status": "MISSING",
                    "error": f"No test definition for {test_ref}",
                }
            else:
                outcome = self._run_single_test(test_def["function"])

            database.insert_evidence(
                self.db_path,
                req_id=req["id"],
                test_ref=test_ref,
                status=outcome["status"],
                error=outcome["error"],
                timestamp=now,
            )

        return self.get_matrix()

    def _format_evidence_id(self, raw_id):
        return f"EVID-{raw_id:03d}"

    def get_matrix(self):
        """Return the full traceability matrix: requirements joined with their latest evidence."""
        matrix = []
        for req in self.requirements:
            latest = database.get_latest_evidence_for(self.db_path, req["id"])
            if latest is None:
                status, error, last_run, evidence_id = "NOT RUN", None, None, None
            else:
                status = latest["status"]
                error = latest["error"]
                last_run = latest["timestamp"]
                evidence_id = self._format_evidence_id(latest["evidence_id"])

            matrix.append(
                {
                    "id": req["id"],
                    "description": req["description"],
                    "category": req["category"],
                    "test_ref": req.get("test_ref"),
                    "status": status,
                    "error": error,
                    "last_run": last_run,
                    "evidence_id": evidence_id,
                }
            )
        return matrix

    def summary(self):
        """Return pass/fail counts across the current matrix."""
        matrix = self.get_matrix()
        counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "MISSING": 0, "NOT RUN": 0}
        for row in matrix:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        return counts

    def get_evidence_log(self):
        """Return the full history of every evidence record ever recorded."""
        raw_log = database.get_all_evidence(self.db_path)
        for entry in raw_log:
            entry["evidence_id"] = self._format_evidence_id(entry["evidence_id"])
        return raw_log
