"""Run the whole pipeline (or selected phases) with the checked-in configurations.

    .venv/Scripts/python.exe run_all.py                 # everything
    .venv/Scripts/python.exe run_all.py --phases 1,2,3  # selected phases
    .venv/Scripts/python.exe run_all.py --list

Each step is a separate process so one failure never hides the others; the summary written to
results/run_all_<timestamp>.json records the exit code of every step.  A non-zero exit code of
the test step is EXPECTED: tests marked paper_claim assert statements of the paper that do not
hold (see results/tests/test_report.json and reports/).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
# WSL2 (lightning.gpu) steps: the project as seen from Linux, e.g. C:/x/y -> /mnt/c/x/y
WSL_ROOT = "/mnt/" + ROOT.drive[0].lower() + ROOT.as_posix()[2:]
WSL_PY = "~/venvs/epsqec/bin/python"


def wsl(script: str) -> list[str]:
    return ["wsl", "-d", "Ubuntu", "--cd", WSL_ROOT, "--", "bash", "-lc", f"{WSL_PY} -u {script}"]

STEPS = [
    ("1", "phase1_original", [PY, "experiments/phase1_original.py"]),
    ("1", "phase1_fixed_impact", [PY, "experiments/phase1_fixed_impact.py"]),
    ("2", "phase2_algebra", [PY, "experiments/phase2_algebra.py"]),
    ("3", "extract_paper_figures", [PY, "experiments/extract_paper_figures.py"]),
    ("3", "phase3_awgn", [PY, "experiments/phase3_awgn.py"]),
    ("3", "plot_awgn", [PY, "experiments/plot_awgn.py"]),
    ("4", "phase4_stabilizer", [PY, "experiments/phase4_stabilizer.py"]),
    ("4", "phase4_supplement", [PY, "experiments/phase4_supplement.py"]),
    ("5", "phase5_prop5", [PY, "experiments/phase5_prop5.py"]),
    ("5", "phase5_pennylane", [PY, "experiments/phase5_pennylane.py"]),
    ("6", "phase6_noise", [PY, "experiments/phase6_noise.py"]),
    ("6", "plot_noise", [PY, "experiments/plot_noise.py"]),
    ("B", "bench_cpu_gpu", [PY, "experiments/bench_cpu_gpu.py"]),
    # second-author review + gate-level specification
    ("V", "review_checks", [PY, "experiments/review_checks.py"]),
    ("V", "zreading_condition", [PY, "experiments/zreading_condition.py"]),
    ("G", "gate_level_css", [PY, "experiments/gate_level_css.py"]),
    ("G", "noise_layouts", [PY, "experiments/noise_layouts.py"]),
    ("G", "mc_seed_check", [PY, "experiments/mc_seed_check.py"]),
    ("G", "qudit_depolarizing_mc", [PY, "experiments/qudit_depolarizing_mc.py"]),
    ("R", "apply_review_changes", [PY, "experiments/apply_review_changes.py"]),
    ("W", "wsl_verify_gpu", wsl("wsl/verify_wsl_gpu.py")),
    ("W", "wsl_phase5_pennylane_gpu", wsl("experiments/phase5_pennylane.py --config phase5_pennylane_gpu.toml "
                                          "--only gates,prop5,xsyn,cycle,cycle_coherent")),
    ("W", "wsl_bench_pennylane_devices", wsl("experiments/bench_pennylane_devices.py")),
    ("T", "pytest", [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider"]),
    ("R", "draw_circuits", [PY, "experiments/draw_circuits.py"]),
    ("R", "make_report", [PY, "experiments/make_report.py"]),
    ("R", "make_pdf", [PY, "experiments/make_pdf.py"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", default=None, help="comma list among 1,2,3,4,5,6,B,W,V,G,T,R (W needs WSL2, see wsl/setup_wsl_gpu.sh)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for p, name, cmd in STEPS:
            print(p, name, " ".join(cmd[1:]))
        return
    sel = set(a.phases.split(",")) if a.phases else None
    summary = []
    for p, name, cmd in STEPS:
        if sel and p not in sel:
            continue
        print(f"\n=== [{p}] {name}: {' '.join(cmd[1:])}", flush=True)
        t = time.perf_counter()
        rc = subprocess.call(cmd, cwd=ROOT)
        summary.append({"phase": p, "step": name, "exit_code": rc, "seconds": round(time.perf_counter() - t, 1)})
        print(f"=== [{p}] {name}: exit {rc} in {summary[-1]['seconds']} s", flush=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "results" / f"run_all_{stamp}.json"
    out.write_text(json.dumps(summary, indent=2))
    print("\nsummary ->", out)
    for s in summary:
        print(f"  [{s['phase']}] {s['step']:<20} exit {s['exit_code']}  {s['seconds']} s")


if __name__ == "__main__":
    main()
