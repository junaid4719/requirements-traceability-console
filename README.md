# Requirements Traceability Console

A live web dashboard that links software requirements directly to the tests that verify them, and shows real pass/fail status at a glance — a small-scale implementation of the bidirectional requirements traceability used in automotive software validation (ISO 26262 / ASPICE-style workflows).

## Why this project

In automotive and other safety-relevant software, every requirement needs to be traceable to evidence that it's actually been verified — "did we test Requirement 42, and did it pass?" should be answerable in seconds, not by digging through spreadsheets. This project builds that idea directly: requirements are defined in a structured file, each linked to a real automated test, and a live dashboard shows the current verification status of every one of them — re-runnable at the click of a button.

It also builds on the [Vehicle Log Analyser](https://github.com/junaid4719/vehicle-log-analyser) project — the tests here exercise that project's real fault-detection logic, not a mock.

## How it works

```
requirements.json (what must be true)
              ↓
   linked to a real test function
              ↓
   Traceability Engine runs the test
              ↓
   PASS / FAIL / ERROR recorded with a timestamp
              ↓
   Flask API serves the live matrix
              ↓
   Dashboard renders it, with a Run All Tests button
```

## Features

- **Bidirectional traceability** — every requirement points to a test; every result points back to a requirement
- **Live re-run from the browser** — no terminal needed to re-verify requirements
- **Real verification, not a mock** — the linked tests exercise actual Vehicle Log Analyser logic
- **Structured requirement data** — requirements defined in JSON, easy to extend without touching code
- **Automated dependency vulnerability scanning** — CI runs `pip-audit` against every dependency on every push, in line with continuous vulnerability management practices (ISO/SAE 21434)
- **Unit tested** — the traceability engine itself is covered by a `pytest` suite

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

Then open **http://127.0.0.1:5000** in a browser. Click **"Run All Tests"** to execute every linked test live and see the matrix update with real results.

## Running the tests

```bash
pytest test_traceability_engine.py -v
pytest test_requirements.py -v
```

## Project structure

```
requirements-traceability-console/
├── app.py                        # Flask backend and API routes
├── traceability_engine.py        # Core traceability logic: runs tests, builds the matrix
├── requirements.json             # Requirement definitions, each linked to a test_id
├── test_requirements.py          # The actual verification tests, linked from requirements.json
├── test_traceability_engine.py   # Unit tests for the engine itself
├── log_analyser.py               # Reused component from the Vehicle Log Analyser project
├── templates/
│   └── dashboard.html            # Frontend dashboard UI
├── requirements.txt              # Python dependencies
└── README.md
```

## Possible future improvements

- Persist run history so trends over time are visible, not just the latest run
- Add severity levels to requirements (critical / major / minor)
- Export the traceability matrix as a PDF or CSV report for audit purposes
- Integrate with the existing CI pipeline so the matrix updates automatically on every push

## License

MIT
