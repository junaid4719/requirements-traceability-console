"""
Unit tests for the Traceability Engine.
Run with: pytest test_traceability_engine.py
"""

import json
import pytest
from traceability_engine import TraceabilityEngine


@pytest.fixture
def sample_paths(tmp_path):
    reqs = [
        {
            "id": "REQ-001",
            "description": "Engine temperature must not exceed 110C.",
            "category": "Powertrain Safety",
            "test_ref": "TEST-001",
        },
        {
            "id": "REQ-999",
            "description": "A requirement with no matching test definition.",
            "category": "Edge Case",
            "test_ref": "TEST-999",
        },
    ]
    tests = [
        {
            "id": "TEST-001",
            "function": "test_engine_temp_within_threshold",
            "description": "Verifies engine temperature stays within threshold",
        },
        # Deliberately no TEST-999, to test the MISSING case
    ]

    reqs_path = tmp_path / "requirements.json"
    tests_path = tmp_path / "tests.json"
    with open(reqs_path, "w") as f:
        json.dump(reqs, f)
    with open(tests_path, "w") as f:
        json.dump(tests, f)

    return str(reqs_path), str(tests_path)


def test_loads_requirements_and_tests(sample_paths):
    reqs_path, tests_path = sample_paths
    engine = TraceabilityEngine(requirements_path=reqs_path, tests_path=tests_path)
    assert len(engine.requirements) == 2
    assert engine.requirements[0]["id"] == "REQ-001"
    assert "TEST-001" in engine.tests_by_id


def test_matrix_before_run_shows_not_run(sample_paths):
    reqs_path, tests_path = sample_paths
    engine = TraceabilityEngine(requirements_path=reqs_path, tests_path=tests_path)
    matrix = engine.get_matrix()
    assert all(row["status"] == "NOT RUN" for row in matrix)


def test_run_all_produces_pass_for_valid_requirement(sample_paths):
    reqs_path, tests_path = sample_paths
    engine = TraceabilityEngine(requirements_path=reqs_path, tests_path=tests_path)
    matrix = engine.run_all()
    req_001 = next(r for r in matrix if r["id"] == "REQ-001")
    assert req_001["status"] == "PASS"
    assert req_001["last_run"] is not None
    assert req_001["evidence_id"] is not None


def test_missing_test_definition_reports_missing(sample_paths):
    reqs_path, tests_path = sample_paths
    engine = TraceabilityEngine(requirements_path=reqs_path, tests_path=tests_path)
    matrix = engine.run_all()
    req_999 = next(r for r in matrix if r["id"] == "REQ-999")
    assert req_999["status"] == "MISSING"
    assert req_999["error"] is not None


def test_summary_counts_match_matrix(sample_paths):
    reqs_path, tests_path = sample_paths
    engine = TraceabilityEngine(requirements_path=reqs_path, tests_path=tests_path)
    engine.run_all()
    summary = engine.summary()
    assert summary["PASS"] == 1
    assert summary["MISSING"] == 1


def test_evidence_log_records_every_run(sample_paths):
    reqs_path, tests_path = sample_paths
    engine = TraceabilityEngine(requirements_path=reqs_path, tests_path=tests_path)
    engine.run_all()
    engine.run_all()
    log = engine.get_evidence_log()
    # 2 requirements x 2 runs = 4 evidence entries
    assert len(log) == 4
    assert log[0]["evidence_id"] == "EVID-001"
    assert log[-1]["evidence_id"] == "EVID-004"
