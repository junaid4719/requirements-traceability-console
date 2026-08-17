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
            "test_refs": ["TEST-001"],
        },
        {
            "id": "REQ-002",
            "description": "Requires two tests to fully verify.",
            "category": "Fault Detection",
            "test_refs": ["TEST-001", "TEST-002"],
        },
        {
            "id": "REQ-999",
            "description": "A requirement with no matching test definition.",
            "category": "Edge Case",
            "test_refs": ["TEST-999"],
        },
        {
            "id": "REQ-ORPHAN",
            "description": "A requirement with no linked test at all.",
            "category": "Edge Case",
            "test_refs": [],
        },
    ]
    tests = [
        {
            "id": "TEST-001",
            "function": "test_engine_temp_within_threshold",
            "description": "Verifies engine temperature stays within threshold",
        },
        {
            "id": "TEST-002",
            "function": "test_rpm_within_threshold",
            "description": "Verifies engine RPM stays within threshold",
        },
        {
            "id": "TEST-UNUSED",
            "function": "test_no_false_positives",
            "description": "Not referenced by any requirement, to test orphan test detection",
        },
        # Deliberately no TEST-999, to test the MISSING case
    ]

    reqs_path = tmp_path / "requirements.json"
    tests_path = tmp_path / "tests.json"
    db_path = tmp_path / "test_traceability.db"

    with open(reqs_path, "w") as f:
        json.dump(reqs, f)
    with open(tests_path, "w") as f:
        json.dump(tests, f)

    return str(reqs_path), str(tests_path), str(db_path)


def _make_engine(sample_paths):
    reqs_path, tests_path, db_path = sample_paths
    return TraceabilityEngine(
        requirements_path=reqs_path, tests_path=tests_path, db_path=db_path
    )


def test_loads_requirements_and_tests(sample_paths):
    engine = _make_engine(sample_paths)
    assert len(engine.requirements) == 4
    assert "TEST-001" in engine.tests_by_id


def test_matrix_before_run_shows_not_run(sample_paths):
    engine = _make_engine(sample_paths)
    matrix = engine.get_matrix()
    assert all(row["status"] == "NOT RUN" for row in matrix)


def test_single_test_requirement_passes(sample_paths):
    engine = _make_engine(sample_paths)
    matrix = engine.run_all()
    req_001 = next(r for r in matrix if r["id"] == "REQ-001")
    assert req_001["status"] == "PASS"
    assert len(req_001["evidence_ids"]) == 1


def test_multi_test_requirement_passes_only_if_all_tests_pass(sample_paths):
    engine = _make_engine(sample_paths)
    matrix = engine.run_all()
    req_002 = next(r for r in matrix if r["id"] == "REQ-002")
    # Both TEST-001 and TEST-002 should pass, so overall status is PASS
    assert req_002["status"] == "PASS"
    assert len(req_002["evidence_ids"]) == 2


def test_missing_test_definition_reports_missing(sample_paths):
    engine = _make_engine(sample_paths)
    matrix = engine.run_all()
    req_999 = next(r for r in matrix if r["id"] == "REQ-999")
    assert req_999["status"] == "MISSING"


def test_orphan_requirement_reports_missing_after_run(sample_paths):
    engine = _make_engine(sample_paths)
    matrix = engine.run_all()
    req_orphan = next(r for r in matrix if r["id"] == "REQ-ORPHAN")
    assert req_orphan["status"] == "MISSING"


def test_get_orphans_detects_unlinked_requirement_and_unused_test(sample_paths):
    engine = _make_engine(sample_paths)
    orphans = engine.get_orphans()
    assert "REQ-ORPHAN" in orphans["orphan_requirements"]
    assert "TEST-UNUSED" in orphans["orphan_tests"]


def test_summary_counts_match_matrix(sample_paths):
    engine = _make_engine(sample_paths)
    engine.run_all()
    summary = engine.summary()
    matrix = engine.get_matrix()
    total_from_summary = sum(summary.values())
    assert total_from_summary == len(matrix)


def test_evidence_persists_after_new_engine_instance(sample_paths):
    """Phase 2 regression check: evidence still survives creating a fresh engine."""
    reqs_path, tests_path, db_path = sample_paths
    engine1 = TraceabilityEngine(
        requirements_path=reqs_path, tests_path=tests_path, db_path=db_path
    )
    engine1.run_all()

    engine2 = TraceabilityEngine(
        requirements_path=reqs_path, tests_path=tests_path, db_path=db_path
    )
    matrix = engine2.get_matrix()
    req_001 = next(r for r in matrix if r["id"] == "REQ-001")
    assert req_001["status"] == "PASS"
