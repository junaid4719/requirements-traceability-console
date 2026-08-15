"""
Unit tests for the Traceability Engine.
Run with: pytest test_traceability_engine.py
"""

import json
import pytest
from traceability_engine import TraceabilityEngine


@pytest.fixture
def sample_requirements(tmp_path):
    reqs = [
        {
            "id": "REQ-001",
            "description": "Engine temperature must not exceed 110C.",
            "category": "Powertrain Safety",
            "test_id": "test_engine_temp_within_threshold",
        },
        {
            "id": "REQ-999",
            "description": "A requirement with no matching test function.",
            "category": "Edge Case",
            "test_id": "test_does_not_exist_anywhere",
        },
    ]
    path = tmp_path / "requirements.json"
    with open(path, "w") as f:
        json.dump(reqs, f)
    return str(path)


def test_loads_requirements(sample_requirements):
    engine = TraceabilityEngine(requirements_path=sample_requirements)
    assert len(engine.requirements) == 2
    assert engine.requirements[0]["id"] == "REQ-001"


def test_matrix_before_run_shows_not_run(sample_requirements):
    engine = TraceabilityEngine(requirements_path=sample_requirements)
    matrix = engine.get_matrix()
    assert all(row["status"] == "NOT RUN" for row in matrix)


def test_run_all_produces_pass_for_valid_requirement(sample_requirements):
    engine = TraceabilityEngine(requirements_path=sample_requirements)
    matrix = engine.run_all()
    req_001 = next(r for r in matrix if r["id"] == "REQ-001")
    assert req_001["status"] == "PASS"
    assert req_001["last_run"] is not None


def test_missing_test_function_reports_missing(sample_requirements):
    engine = TraceabilityEngine(requirements_path=sample_requirements)
    matrix = engine.run_all()
    req_999 = next(r for r in matrix if r["id"] == "REQ-999")
    assert req_999["status"] == "MISSING"
    assert req_999["error"] is not None


def test_summary_counts_match_matrix(sample_requirements):
    engine = TraceabilityEngine(requirements_path=sample_requirements)
    engine.run_all()
    summary = engine.summary()
    assert summary["PASS"] == 1
    assert summary["MISSING"] == 1
