"""
Requirement Verification Tests
--------------------------------
Each test function here is linked to a specific requirement in
requirements.json via its function name (the "test_id" field).
These tests exercise the real VehicleLogAnalyser logic to prove
each requirement is actually met — this is not a mock suite.
"""

import csv
from log_analyser import VehicleLogAnalyser


def _write_log(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_engine_temp_within_threshold(tmp_path):
    """REQ-001: engine temp above 110C must be flagged as a fault."""
    log_path = tmp_path / "log.csv"
    _write_log(
        str(log_path),
        [
            {
                "timestamp": "t1",
                "engine_temp_c": "115",
                "rpm": "2000",
                "speed_kph": "50",
                "battery_voltage": "12.6",
            },
        ],
    )
    analyser = VehicleLogAnalyser(
        log_file=str(log_path), thresholds_path=str(tmp_path / "thresholds.json")
    )
    analyser.analyse()
    assert any(f["field"] == "engine_temp_c" for f in analyser.faults)


def test_rpm_within_threshold(tmp_path):
    """REQ-002: RPM above 6500 must be flagged as a fault."""
    log_path = tmp_path / "log.csv"
    _write_log(
        str(log_path),
        [
            {
                "timestamp": "t1",
                "engine_temp_c": "90",
                "rpm": "7200",
                "speed_kph": "50",
                "battery_voltage": "12.6",
            },
        ],
    )
    analyser = VehicleLogAnalyser(
        log_file=str(log_path), thresholds_path=str(tmp_path / "thresholds.json")
    )
    analyser.analyse()
    assert any(f["field"] == "rpm" for f in analyser.faults)


def test_battery_voltage_within_threshold(tmp_path):
    """REQ-003: battery voltage outside 11.5-14.8V must be flagged."""
    log_path = tmp_path / "log.csv"
    _write_log(
        str(log_path),
        [
            {
                "timestamp": "t1",
                "engine_temp_c": "90",
                "rpm": "2000",
                "speed_kph": "50",
                "battery_voltage": "10.2",
            },
        ],
    )
    analyser = VehicleLogAnalyser(
        log_file=str(log_path), thresholds_path=str(tmp_path / "thresholds.json")
    )
    analyser.analyse()
    assert any(f["field"] == "battery_voltage" for f in analyser.faults)


def test_all_faults_detected(tmp_path):
    """REQ-004: every out-of-range reading in a log must be caught, none missed."""
    log_path = tmp_path / "log.csv"
    _write_log(
        str(log_path),
        [
            {
                "timestamp": "t1",
                "engine_temp_c": "115",
                "rpm": "7200",
                "speed_kph": "50",
                "battery_voltage": "10.2",
            },
            {
                "timestamp": "t2",
                "engine_temp_c": "90",
                "rpm": "2000",
                "speed_kph": "50",
                "battery_voltage": "12.6",
            },
        ],
    )
    analyser = VehicleLogAnalyser(
        log_file=str(log_path), thresholds_path=str(tmp_path / "thresholds.json")
    )
    analyser.analyse()
    # row 1 has 3 faults (temp, rpm, battery), row 2 has 0
    assert len(analyser.faults) == 3


def test_no_false_positives(tmp_path):
    """REQ-005: a log with entirely valid readings must produce zero faults."""
    log_path = tmp_path / "log.csv"
    _write_log(
        str(log_path),
        [
            {
                "timestamp": "t1",
                "engine_temp_c": "90",
                "rpm": "2000",
                "speed_kph": "50",
                "battery_voltage": "12.6",
            },
            {
                "timestamp": "t2",
                "engine_temp_c": "85",
                "rpm": "1800",
                "speed_kph": "40",
                "battery_voltage": "12.8",
            },
        ],
    )
    analyser = VehicleLogAnalyser(
        log_file=str(log_path), thresholds_path=str(tmp_path / "thresholds.json")
    )
    analyser.analyse()
    assert len(analyser.faults) == 0


def test_missing_file_handled_gracefully(tmp_path):
    """REQ-006: a missing log file must not crash the system."""
    fake_path = str(tmp_path / "does_not_exist.csv")
    analyser = VehicleLogAnalyser(
        log_file=fake_path, thresholds_path=str(tmp_path / "thresholds.json")
    )
    analyser.analyse()  # should log an error, not raise
    assert analyser.faults == []


def test_fault_includes_row_and_timestamp(tmp_path):
    """REQ-007: every fault must carry a row number and timestamp for traceability."""
    log_path = tmp_path / "log.csv"
    _write_log(
        str(log_path),
        [
            {
                "timestamp": "2026-01-01T10:00:00",
                "engine_temp_c": "120",
                "rpm": "2000",
                "speed_kph": "50",
                "battery_voltage": "12.6",
            },
        ],
    )
    analyser = VehicleLogAnalyser(
        log_file=str(log_path), thresholds_path=str(tmp_path / "thresholds.json")
    )
    analyser.analyse()
    fault = analyser.faults[0]
    assert fault["row"] == 1
    assert fault["timestamp"] == "2026-01-01T10:00:00"
