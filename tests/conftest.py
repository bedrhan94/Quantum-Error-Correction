"""Shared fixtures + a reporter that writes results/tests/test_report.{json,csv}.

Outcome mapping:  passed -> PASS, failed/error -> FAIL, skipped -> NOT RUN.
Failure classification (field "failure_class"):
  * tests marked @pytest.mark.paper_claim assert a statement of the paper *as written*; when they
    fail the cause is classified "mathematical (paper claim does not hold)";
  * tests marked @pytest.mark.definition_consistency read a statement with the other of the two dual
    definitions the paper uses; failures are "mathematical (paper definitions mutually inconsistent)";
  * tests marked @pytest.mark.original_source exercise the authors' unchanged code; failures are
    "implementation (original source)";
  * skipped tests carry their skip reason (environment, e.g. no CUDA / PennyLane);
  * every other failure is "implementation (this project)".
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_RESULTS: list[dict] = []


MATH_MARKERS = ("paper_claim", "definition_consistency", "math", "outside_hypothesis")


def pytest_configure(config):
    for m in ("paper_claim: asserts a statement of the paper literally",
              "definition_consistency: checks a statement under the OTHER dual definition used in the paper",
              "outside_hypothesis: paper statement about a case outside the paper's own hypotheses",
              "math: mathematical fact checked by enumeration (not a statement of the paper)",
              "original_source: exercises the authors' unchanged code",
              "slow: long running", "gpu: needs CUDA", "pennylane: needs PennyLane"):
        config.addinivalue_line("markers", m)


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        item_markers = getattr(report, "_markers", [])
        outcome = {"passed": "PASS", "failed": "FAIL", "skipped": "NOT RUN"}[report.outcome]
        category = "matematiksel iddia" if any(m in item_markers for m in MATH_MARKERS) else "uygulama"
        cls = None
        if outcome == "FAIL":
            if "outside_hypothesis" in item_markers:
                cls = "mathematical (paper table entry; case outside the paper's own hypothesis)"
            elif "paper_claim" in item_markers:
                cls = "mathematical (paper claim does not hold)"
            elif "definition_consistency" in item_markers:
                cls = "mathematical (paper definitions mutually inconsistent)"
            elif "original_source" in item_markers:
                cls = "implementation (original source)"
            else:
                cls = "implementation (this project)"
        elif outcome == "NOT RUN":
            cls = "environment / not executed"
        msg = ""
        if report.longrepr is not None:
            if hasattr(report.longrepr, "reprcrash") and report.longrepr.reprcrash is not None:
                msg = report.longrepr.reprcrash.message
            else:
                msg = str(report.longrepr)
        _RESULTS.append({"test": report.nodeid, "outcome": outcome, "category": category, "failure_class": cls,
                         "message": msg[:500], "duration_s": round(report.duration, 3),
                         "markers": item_markers})


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    rep._markers = [m.name for m in item.iter_markers()]


def pytest_sessionfinish(session, exitstatus):
    out = ROOT / "results" / "tests"
    out.mkdir(parents=True, exist_ok=True)
    summary = {k: sum(r["outcome"] == k for r in _RESULTS) for k in ("PASS", "FAIL", "NOT RUN")}
    by_cat = {c: {k: sum(r["outcome"] == k and r["category"] == c for r in _RESULTS) for k in ("PASS", "FAIL", "NOT RUN")}
              for c in ("matematiksel iddia", "uygulama")}
    payload = {"generated_utc": dt.datetime.now(dt.UTC).isoformat(), "summary": summary,
               "summary_by_category": by_cat, "tests": _RESULTS}
    (out / "test_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with open(out / "test_report.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["test", "outcome", "category", "failure_class", "duration_s", "message"])
        w.writeheader()
        for r in _RESULTS:
            w.writerow({k: r[k] for k in w.fieldnames})


# ----------------------------------------------------------------------------- fixtures
@pytest.fixture(scope="session")
def built():
    from epsqec.css.build import build

    cache = {}

    def get(key):
        if key not in cache:
            spec = {"key": key}
            if key == "Z5_small":
                spec = {"key": key, "q": 5, "alpha1": [2, 1], "alpha2": [1, 0], "eps": "greedy"}
            cache[key] = build(spec)
        return cache[key]

    return get
