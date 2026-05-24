"""
Flask web server for the Stock Analyser dashboard.
"""

import json
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory

from .pipeline import run_pipeline, run_quick, load_config

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent.parent / "templates"),
    static_folder=str(Path(__file__).parent.parent / "static"),
)

OUTPUT_DIR = Path(__file__).parent.parent / "output"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analysis")
def get_analysis():
    """Return latest analysis data."""
    output_file = OUTPUT_DIR / "analysis.json"
    if output_file.exists():
        with open(output_file) as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No analysis data. Run /api/run-quick first."})


@app.route("/api/run-quick", methods=["POST"])
def trigger_quick_run():
    """Trigger a quick analysis run."""
    try:
        result = run_quick()
        return jsonify({"status": "success", "summary": result["summary"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/run-full", methods=["POST"])
def trigger_full_run():
    """Trigger a full analysis run."""
    try:
        result = run_pipeline()
        return jsonify({"status": "success", "summary": result["summary"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/config")
def get_config():
    """Return current config."""
    return jsonify(load_config())


def start_server(port=8400, debug=True):
    print(f"\n  Stock Multibagger Analyser Dashboard")
    print(f"  http://localhost:{port}")
    print(f"  {'='*40}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
