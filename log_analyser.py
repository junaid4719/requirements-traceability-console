"""
Vehicle Log Analyser
---------------------
Reads vehicle diagnostic log files (CSV format), extracts fault
codes and sensor readings outside of safe thresholds, and produces
a summary report. Demonstrates data parsing, rule-based fault
detection, and automated report generation.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path


class VehicleLogAnalyser:
    def __init__(self, log_file: str, thresholds_path: str = "thresholds.json"):
        self.log_file = log_file
        self.thresholds_path = thresholds_path
        self.thresholds = self._load_thresholds()
        self.faults = []
        self._setup_logging()

    def _load_thresholds(self) -> dict:
        """Load safe operating ranges for each sensor from JSON."""
        if not Path(self.thresholds_path).exists():
            default_thresholds = {
                "engine_temp_c": {"min": 0, "max": 110},
                "rpm": {"min": 0, "max": 6500},
                "speed_kph": {"min": 0, "max": 220},
                "battery_voltage": {"min": 11.5, "max": 14.8},
            }
            with open(self.thresholds_path, "w") as f:
                json.dump(default_thresholds, f, indent=4)
            return default_thresholds

        with open(self.thresholds_path, "r") as f:
            return json.load(f)

    def _setup_logging(self):
        logging.basicConfig(
            filename="log_analyser.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def analyse(self):
        """Read the log file and check every row against thresholds."""
        if not Path(self.log_file).exists():
            self.logger.error(f"Log file not found: {self.log_file}")
            print(f"Error: log file not found -> {self.log_file}")
            return

        with open(self.log_file, newline="") as f:
            reader = csv.DictReader(f)

            for row_number, row in enumerate(reader, start=1):
                self._check_row(row_number, row)

        self.logger.info(f"Analysis complete. {len(self.faults)} fault(s) found.")

    def _check_row(self, row_number: int, row: dict):
        """Check a single row of log data against configured thresholds."""
        for field, limits in self.thresholds.items():
            if field not in row:
                continue

            try:
                value = float(row[field])
            except (ValueError, TypeError):
                continue  # skip rows with missing/malformed data

            if value < limits["min"] or value > limits["max"]:
                fault = {
                    "row": row_number,
                    "timestamp": row.get("timestamp", "unknown"),
                    "field": field,
                    "value": value,
                    "expected_range": f"{limits['min']} - {limits['max']}",
                }
                self.faults.append(fault)
                self.logger.warning(
                    f"Fault detected at row {row_number}: {field}={value} "
                    f"(expected {limits['min']}-{limits['max']})"
                )

    def generate_report(self, output_path: str = "fault_report.txt"):
        """Write a human-readable summary report of all faults found."""
        with open(output_path, "w") as f:
            f.write("VEHICLE LOG ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Source file: {self.log_file}\n")
            f.write(f"Total faults found: {len(self.faults)}\n")
            f.write("-" * 50 + "\n\n")

            if not self.faults:
                f.write("No faults detected. All readings within safe range.\n")
            else:
                for fault in self.faults:
                    f.write(
                        f"Row {fault['row']} | Timestamp: {fault['timestamp']} | "
                        f"{fault['field']} = {fault['value']} "
                        f"(expected {fault['expected_range']})\n"
                    )

        print(f"Report written to {output_path}")
        return output_path


if __name__ == "__main__":
    analyser = VehicleLogAnalyser(log_file="sample_vehicle_log.csv")
    analyser.analyse()
    analyser.generate_report()
