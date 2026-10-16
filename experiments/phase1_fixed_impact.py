"""Measure the impact of the minimal fix of the authors' hermitian_dual() (kept separately in
original_source_fixed/; original_source/ is untouched).

    .venv/Scripts/python.exe experiments/phase1_fixed_impact.py
1. writes original_source_fixed/hermitian_dual_fix.diff (unified diff vs the original file);
2. runs both files' __main__ blocks and compares stdout byte for byte;
3. compares duals and double duals of both versions with the independent implementation.
"""
from __future__ import annotations

import difflib
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np

from epsqec.benchmarking import Experiment
from epsqec.ideals import AdditiveCode, hermitian_dual
from epsqec.original_bridge import ORIGINAL_FILE, original_code_to_indices, sha256
from epsqec.ring import GaussianRing

ROOT = Path(__file__).resolve().parents[1]
FIXED = ROOT / "original_source_fixed" / "epsilon_codes_fixed.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    cases = [{"q": 5, "gen": [[2, 1], [1, 0]]}, {"q": 5, "gen": [[1, 2], [3, 4]]}, {"q": 13, "gen": [[3, 2], [1, 1]]}]
    cfg = {"cases": cases, "seed": 0}
    with Experiment("original", "phase1_fixed_impact", cfg, seed=0) as ex:
        a = ORIGINAL_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
        b = FIXED.read_text(encoding="utf-8").splitlines(keepends=True)
        diff = "".join(difflib.unified_diff(a, b, "original_source/epsilon codes.py", "original_source_fixed/epsilon_codes_fixed.py"))
        (FIXED.parent / "hermitian_dual_fix.diff").write_text(diff, encoding="utf-8")
        outs = {}
        for tag, path in (("original", ORIGINAL_FILE), ("fixed", FIXED)):
            r = subprocess.run([sys.executable, "-I", str(path)], capture_output=True, text=True, timeout=600)
            outs[tag] = r.stdout
        res = {"original_sha256": sha256(ORIGINAL_FILE), "fixed_sha256": sha256(FIXED),
               "diff_lines": sum(1 for line in diff.splitlines() if line[:1] in "+-" and line[:3] not in ("+++", "---")),
               "main_stdout_identical": outs["original"] == outs["fixed"], "cases": []}
        orig, fixd = load(ORIGINAL_FILE, "orig_mod"), load(FIXED, "fixed_mod")
        for c in cases:
            q = c["q"]
            R = GaussianRing(q)
            C = AdditiveCode.submodule(R, np.array([c["gen"]]))
            D, DD = hermitian_dual(C), hermitian_dual(hermitian_dual(C))
            row = {"q": q, "gen": c["gen"], "|C|": C.size}
            for tag, mod in (("original", orig), ("fixed", fixd)):
                Co = mod.GaussianCodeN([tuple(p) for p in c["gen"]], q)
                Do = Co.hermitian_dual()
                row[f"{tag}_dual_equals_independent"] = bool(np.array_equal(original_code_to_indices(Do, q), D.indices))
                if q <= 5:
                    DDo = Do.hermitian_dual()
                    row[f"{tag}_double_dual_size"] = DDo.size()
                    row[f"{tag}_double_dual_equals_C"] = bool(np.array_equal(original_code_to_indices(DDo, q), DD.indices))
            res["cases"].append(row)
        ex.save_json("results.json", res)
        if not res["main_stdout_identical"]:
            ex.note("fix changes the output of the authors' __main__ (paper examples)")
        print(res)


if __name__ == "__main__":
    main()
