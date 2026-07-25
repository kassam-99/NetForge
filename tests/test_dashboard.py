"""Tests for the NetForge dashboard launcher (dashboard.py).

These exercise the shared dashboard contract:
  * `python3 dashboard.py --demo` runs the real features end-to-end and exits 0
  * `python3 dashboard.py < /dev/null` is EOF/pipe-safe and exits promptly
Plus a direct call into the real loopback self-test helper.
"""
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD = os.path.join(PROJECT_ROOT, "dashboard.py")
PY = sys.executable


def test_dashboard_help_exits_zero():
    proc = subprocess.run(
        [PY, DASHBOARD, "--help"],
        capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 0
    assert "NetForge" in proc.stdout


def test_dashboard_demo_runs_end_to_end():
    proc = subprocess.run(
        [PY, DASHBOARD, "--demo"],
        capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr
    assert "demo complete" in proc.stdout.lower()


def test_dashboard_demo_json_summary():
    import json
    proc = subprocess.run(
        [PY, DASHBOARD, "--demo", "--json"],
        capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["loopback"]["roundtrip_ok"] is True
    assert data["reports"]["records"] == 3


def test_dashboard_eof_safe_exits_promptly():
    with open(os.devnull, "rb") as devnull:
        proc = subprocess.run(
            [PY, DASHBOARD],
            stdin=devnull, capture_output=True, text=True,
            timeout=12, cwd=PROJECT_ROOT,
        )
    assert proc.returncode == 0
    # Output must stay bounded (well under 1 MB).
    assert len(proc.stdout) + len(proc.stderr) < 100_000


def test_loopback_selftest_helper():
    sys.path.insert(0, PROJECT_ROOT)
    import dashboard
    res = dashboard.run_loopback_selftest(verbose=False)
    assert res["upload_ok"] and res["download_ok"] and res["roundtrip_ok"]
    assert res["uploaded_bytes"] == res["downloaded_bytes"] > 0
