"""
Traceability Engine
----------------------
Loads requirements.json and tests.json, runs the linked test(s) for
each requirement (from test_requirements.py), and permanently
records every run as an evidence entry in a local SQLite database.
Supports many-to-many linking: one requirement can reference several
tests, and one test can be shared across several requirements.
Also detects orphans — requirements with no linked test, and tests
that no requirement references.
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

    def _rollup_status(self, statuses):
        """Combine multiple test statuses into one overall status for a requirement."""
        if not statuses:
            return "MISSING"
        if "MISSING" in statuses:
            return "MISSING"
        if "ERROR" in statuses:
            return "ERROR"
        if "FAIL" in statuses:
            return "FAIL"
        return "PASS"

    def run_all(self):
        """Run every requirement's linked test(s) and permanently record each result."""
        now = datetime.now().isoformat(timespec="seconds")
        for req in self.requirements:
            test_refs = req.get("test_refs", [])
            for test_ref in test_refs:
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

            if not test_refs:
                database.insert_evidence(
                    self.db_path,
                    req_id=req["id"],
                    test_ref=None,
                    status="MISSING",
                    error="No test linked to this requirement",
                    timestamp=now,
                )

        return self.get_matrix()

    def _format_evidence_id(self, raw_id):
        return f"EVID-{raw_id:03d}"

    def get_matrix(self):
        """Return the full traceability matrix: requirements joined with their latest evidence."""
        matrix = []
        for req in self.requirements:
            test_refs = req.get("test_refs", [])

            if test_refs:
                latest_records = [
                    database.get_latest_evidence_for(self.db_path, req["id"], test_ref)
                    for test_ref in test_refs
                ]
            else:
                orphan_record = database.get_latest_evidence_for(
                    self.db_path, req["id"], None
                )
                latest_records = [orphan_record] if orphan_record else []

            latest_records = [r for r in latest_records if r is not None]

            if not latest_records:
                status, error, last_run, evidence_ids = "NOT RUN", None, None, []
            else:
                statuses = [r["status"] for r in latest_records]
                status = self._rollup_status(statuses)
                errors = [r["error"] for r in latest_records if r["error"]]
                error = "; ".join(errors) if errors else None
                last_run = max(r["timestamp"] for r in latest_records)
                evidence_ids = [
                    self._format_evidence_id(r["evidence_id"]) for r in latest_records
                ]

            matrix.append(
                {
                    "id": req["id"],
                    "description": req["description"],
                    "category": req["category"],
                    "test_refs": test_refs,
                    "status": status,
                    "error": error,
                    "last_run": last_run,
                    "evidence_ids": evidence_ids,
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

    def get_orphans(self):
        """Detect orphan requirements (no linked test) and orphan tests (linked by nothing)."""
        orphan_requirements = [
            req["id"] for req in self.requirements if not req.get("test_refs")
        ]

        referenced_test_ids = set()
        for req in self.requirements:
            referenced_test_ids.update(req.get("test_refs", []))

        orphan_tests = [
            test["id"] for test in self.tests if test["id"] not in referenced_test_ids
        ]

        return {
            "orphan_requirements": orphan_requirements,
            "orphan_tests": orphan_tests,
        }
