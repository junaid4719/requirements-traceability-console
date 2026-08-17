# Requirements Traceability Console

A live web dashboard that links software requirements directly to the tests that verify them, and shows real pass/fail status at a glance — a small-scale demonstration of the bidirectional requirements traceability concept used in automotive software validation, in the spirit of ISO 26262 / ASPICE-style workflows.

## Why this project

In automotive and other safety-relevant software, every requirement needs to be traceable to evidence that it's actually been verified — "did we test Requirement 42, and did it pass?" should be answerable in seconds, not by digging through spreadsheets. This project builds that idea directly: requirements are defined in a structured file, each linked to one or more real automated tests via stable engineering IDs, and a live dashboard shows the current verification status of every one of them — re-runnable at the click of a button, with every run permanently recorded as evidence.

It also builds on the [Vehicle Log Analyser](https://github.com/junaid4719/vehicle-log-analyser) project — the tests here exercise that project's real fault-detection logic, not a mock.

## How it works

requirements.json (what must be true, REQ-xxx)
↓
linked via test_refs to one or more entries in tests.json (TEST-xxx)
↓
Traceability Engine runs the linked test(s)
↓
PASS / FAIL / ERROR / MISSING permanently recorded as evidence in SQLite
↓
Flask API serves the live matrix, orphan warnings, and evidence history
↓
Dashboard renders it, with a Run All Tests button
↓
CI generates a traceability evidence report and packages an automated,
versioned GitHub Release on every push to main

## Features

- **Bidirectional, many-to-many traceability** — a requirement can be verified by several tests, and a test can verify several requirements, all linked via stable `REQ-xxx` / `TEST-xxx` IDs rather than raw function names
- **Permanent evidence, not just current status** — every test run is recorded as a timestamped evidence entry in a local SQLite database, so run history survives restarts
- **Orphan detection** — automatically flags requirements with no linked test (coverage gaps) and tests that no requirement references (unused test code)
- **Live re-run from the browser** — no terminal needed to re-verify requirements
- **Real verification, not a mock** — the linked tests exercise actual Vehicle Log Analyser logic
- **Structured requirement and test data** — defined in JSON, easy to extend without touching core logic
- **Automated dependency vulnerability scanning** — CI runs `pip-audit` against every dependency on every push, in the spirit of continuous vulnerability management practices referenced in ISO/SAE 21434
- **Automated source code security scanning** — CI runs `Bandit` against the codebase on every push, catching risky coding patterns (e.g. insecure debug configuration) in addition to dependency checks
- **CI-generated traceability evidence** — every pipeline run produces a structured `traceability-report.json` capturing the full verification state, not just a pass/fail tick
- **Automated release packaging** — on every push to `main`, CI packages a versioned release bundle (code + traceability report) and publishes it as a GitHub Release
- **Unit tested** — the traceability engine, including multi-test rollup, orphan detection, and evidence persistence, is covered by a `pytest` suite

## Requirements

- Python 3.10+
- Flask
- pytest (for running the test suite)

## Installation

```bash
git clone https://github.com/junaid4719/requirements-traceability-console.git
cd requirements-traceability-console
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in a browser. Click **"Run All Tests"** to execute every linked test live and see the matrix, evidence, and any orphan warnings update with real results.

## Running the tests

```bash
pytest test_traceability_engine.py -v
pytest test_requirements.py -v
```

## Generating a traceability report manually

```bash
python generate_report.py
```

Writes a structured `traceability-report.json` — the same report CI generates automatically on every push.

## Project structure

requirements-traceability-console/
├── app.py # Flask backend and API routes
├── traceability_engine.py # Core traceability logic: runs tests, builds the matrix, detects orphans
├── database.py # SQLite persistence layer for evidence records
├── generate_report.py # Generates the CI traceability evidence report
├── requirements.json # Requirement definitions, each linked to one or more test_refs
├── tests.json # Stable test ID definitions, each mapped to a real test function
├── test_requirements.py # The actual verification tests, linked from requirements.json
├── test_traceability_engine.py # Unit tests for the engine itself
├── log_analyser.py # Reused component from the Vehicle Log Analyser project
├── templates/
│ └── dashboard.html # Frontend dashboard UI
├── .github/workflows/ci.yml # CI pipeline: tests, security scans, evidence report, release automation
├── requirements.txt # Python dependencies
└── README.md

## Possible future improvements

- Add severity levels to requirements (critical / major / minor)
- Add change-impact analysis — flag which tests/evidence are affected when a requirement changes
- Export the traceability matrix as a PDF report for audit purposes

## Licence

MIT