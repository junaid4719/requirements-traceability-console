"""
Traceability Dashboard — Flask App
-------------------------------------
Serves a live requirements traceability matrix. Requirements are
loaded from requirements.json, each linked to one or more real test
functions in test_requirements.py. The dashboard shows pass/fail
status per requirement, orphan warnings, and lets you re-run all
tests live from the browser.
"""

import os
from flask import Flask, jsonify, render_template
from traceability_engine import TraceabilityEngine

app = Flask(__name__)
engine = TraceabilityEngine()


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/matrix")
def api_matrix():
    """Return the current traceability matrix (results from the last run, if any)."""
    return jsonify(
        {
            "matrix": engine.get_matrix(),
            "summary": engine.summary(),
            "orphans": engine.get_orphans(),
        }
    )


@app.route("/api/run", methods=["POST"])
def api_run():
    """Re-run every requirement's linked test(s) and return fresh results."""
    matrix = engine.run_all()
    return jsonify(
        {
            "matrix": matrix,
            "summary": engine.summary(),
            "orphans": engine.get_orphans(),
        }
    )


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(debug=debug_mode, port=5000)
