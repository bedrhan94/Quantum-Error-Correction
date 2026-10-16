"""Phase 1 - run the authors' code (unchanged) and test the paper's worked examples with it.

Reproducible command:
    .venv/Scripts/python.exe experiments/phase1_original.py [--config phase1_original.toml]
"""
from __future__ import annotations

import argparse
import contextlib
import io
import random
import time

import numpy as np

from epsqec.benchmarking import Experiment, load_config
from epsqec.css import PAPER_EXAMPLES
from epsqec.decoder import check_transversal
from epsqec.ideals import AdditiveCode, hermitian_dual
from epsqec.original_bridge import (
    APPENDIX_FILE, ORIGINAL_FILE, PAPER_FILE, load_appendix, load_original_module,
    original_code_to_indices, original_vec_to_array, sha256,
)
from epsqec.ring import GaussianRing


def vec(orig, q, pairs):
    return orig.GaussianVector([tuple(p) for p in pairs], q)


def exhaustive_original_decode(orig, app, q, eps, C1o, C2o):
    cnt = {"unique_ok": 0, "unique_wrong": 0, "none_ok": 0, "none_but_y_in_C2": 0,
           "non_unique": 0, "y_in_C2": 0, "y_not_in_C2": 0, "appendix_disagrees": 0}
    t = time.perf_counter()
    tests = 0
    for a in range(q):
        for b in range(q):
            y = orig.GaussianVector([(a, b)], q)
            in_c2 = y in C2o.elements
            cnt["y_in_C2" if in_c2 else "y_not_in_C2"] += 1
            try:
                e, c = orig.decode(y, eps, C1o)
                tests += len(eps)
            except ValueError:
                cnt["non_unique"] += 1
                continue
            if e is None:
                cnt["none_ok" if not in_c2 else "none_but_y_in_C2"] += 1
            else:
                good = (c in C1o.elements) and (c + e == y) and in_c2
                cnt["unique_ok" if good else "unique_wrong"] += 1
            try:
                ea, ca = app.decode(y, eps, C1o, C2o)
                if (ea, ca) != (e, c):
                    cnt["appendix_disagrees"] += 1
            except ValueError:
                cnt["appendix_disagrees"] += 1
    cnt["seconds"] = time.perf_counter() - t
    cnt["membership_tests_source_decode"] = tests
    return cnt


def main(cfg_path: str):
    cfg = load_config(cfg_path)
    with Experiment("original", "phase1_original", cfg, seed=cfg["seed"]) as ex:
        orig = load_original_module()
        app = load_appendix(orig)
        out: dict = {
            "files": {
                "original_source": {"path": str(ORIGINAL_FILE), "sha256": sha256(ORIGINAL_FILE)},
                "appendix_transcription": {"path": str(APPENDIX_FILE), "sha256": sha256(APPENDIX_FILE)},
                "paper_pdf": {"path": str(PAPER_FILE), "sha256": sha256(PAPER_FILE)},
            },
            "examples": {},
        }
        rows = []
        for key in cfg["examples"]:
            pe = PAPER_EXAMPLES[key]
            q = pe.q
            R = GaussianRing(q)
            r: dict = {"q": q, "alpha1": pe.alpha1, "alpha2": pe.alpha2}
            t = time.perf_counter()
            C2o = orig.GaussianCodeN([pe.alpha2], q)
            C1o = orig.GaussianCodeN([pe.alpha1], q)
            r["orig_build_s"] = time.perf_counter() - t
            r["orig_size_C1"], r["orig_size_C2"] = C1o.size(), C2o.size()
            r["orig_nested"] = all(e in C2o.elements for e in C1o.elements)
            # independent enumeration must give identical sets
            C1 = AdditiveCode.principal(R, pe.alpha1)
            C2 = AdditiveCode.principal(R, pe.alpha2)
            r["sets_identical_C1"] = bool(np.array_equal(original_code_to_indices(C1o, q), C1.indices))
            r["sets_identical_C2"] = bool(np.array_equal(original_code_to_indices(C2o, q), C2.indices))
            r["claimed"] = {k: v for k, v in pe.claimed.items() if k.startswith("size") or k in ("index", "K")}
            r["orig_index"] = C2o.size() // C1o.size()

            # ---- eps sets: authors' two procedures, appendix procedure, printed sets
            eps_sets = {
                "orig_find_epsilon_canonical": orig.find_epsilon_canonical(C2o, C1o, q, pe.alpha2),
                "orig_find_epsilon_greedy": orig.find_epsilon(C2o, C1o),
                "appendixA_find_epsilon": app.find_epsilon(C2o, C1o),
            }
            for nm, pairs in pe.eps_sets.items():
                eps_sets[nm] = [vec(orig, q, [p]) for p in pairs]
            r["eps"] = {}
            for nm, eps in eps_sets.items():
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    ok_orig = orig.verify_epsilon(eps, C1o, f"{key}:{nm}")
                arr = np.array([original_vec_to_array(e) for e in eps])
                rep = check_transversal(arr, C2, C1)
                r["eps"][nm] = {
                    "elements": [repr(e) for e in eps],
                    "orig_verify_epsilon_disjoint": ok_orig,
                    "independent_check": rep.as_dict(),
                }
            same = sorted(map(repr, eps_sets["orig_find_epsilon_greedy"])) == sorted(
                map(repr, eps_sets["appendixA_find_epsilon"]))
            r["appendix_find_epsilon_equals_source_find_epsilon"] = same

            # ---- worked decoding examples with the authors' decode()
            checks = []
            for dk in ("decode_example", "decode_example_ex5"):
                if dk not in pe.claimed:
                    continue
                d = pe.claimed[dk]
                eps_name = "paper_example7" if dk == "decode_example" else "paper_example4"
                eps = eps_sets[eps_name]
                y = vec(orig, q, [d["y"]])
                e_src, c_src = orig.decode(y, eps, C1o)
                e_app, c_app = app.decode(y, eps, C1o, C2o)
                exp_e, exp_c = vec(orig, q, [d["e"]]), vec(orig, q, [d["c"]])
                checks.append({
                    "example": dk, "eps": eps_name, "y": repr(y),
                    "expected_e": repr(exp_e), "expected_c": repr(exp_c),
                    "source_decode_e": repr(e_src), "source_decode_c": repr(c_src),
                    "appendix_decode_e": repr(e_app), "appendix_decode_c": repr(c_app),
                    "match_source": bool(e_src == exp_e and c_src == exp_c),
                    "match_appendix": bool(e_app == exp_e and c_app == exp_c),
                    "c_in_C1": c_src in C1o.elements,
                })
            r["worked_examples"] = checks

            # ---- exhaustive decode over every y in R with the authors' decode()
            if cfg["exhaustive_all_R"]:
                for nm in ("orig_find_epsilon_canonical",) + tuple(pe.eps_sets):
                    cnt = exhaustive_original_decode(orig, app, q, eps_sets[nm], C1o, C2o)
                    r.setdefault("exhaustive_all_R", {})[nm] = cnt
                    rows.append({"ring": key, "eps": nm, **cnt})

            # ---- authors' run_simulation with a fixed seed
            random.seed(cfg["seed"])
            sim = orig.run_simulation(q, [pe.alpha2], [pe.alpha1], key, trials=cfg["simulation_trials"])
            r["orig_run_simulation_seeded"] = sim
            out["examples"][key] = r

        # ---- n = 2 Hermitian dual: original vs independent
        duals = []
        for case in cfg["dual_n2_cases"]:
            q = case["q"]
            R = GaussianRing(q)
            t = time.perf_counter()
            Co = orig.GaussianCodeN([tuple(p) for p in case["gen"]], q)
            Do = Co.hermitian_dual()
            t_orig = time.perf_counter() - t
            C = AdditiveCode.submodule(R, np.array([case["gen"]]))
            D = hermitian_dual(C)
            duals.append({
                "q": q, "gen": case["gen"], "orig_dual_size": Do.size(), "indep_dual_size": D.size,
                "identical": bool(np.array_equal(original_code_to_indices(Do, q), D.indices)),
                "orig_seconds": t_orig, "size_C": C.size, "orig_size_C": Co.size(),
            })
        out["dual_n2"] = duals

        # ---- latent-bug probe: dual of the dual with the original class
        dd = cfg["double_dual_case"]
        Co = orig.GaussianCodeN([tuple(p) for p in dd["gen"]], dd["q"])
        Do = Co.hermitian_dual()
        DDo = Do.hermitian_dual()
        R = GaussianRing(dd["q"])
        C = AdditiveCode.submodule(R, np.array([dd["gen"]]))
        DD = hermitian_dual(hermitian_dual(C))
        out["double_dual_probe"] = {
            "size_C": Co.size(), "orig_size_dual": Do.size(), "orig_size_double_dual": DDo.size(),
            "indep_size_double_dual": DD.size, "indep_double_dual_equals_C": DD == C,
            "orig_dual_object_generator": repr(Do.generator),
            "explanation": "hermitian_dual() returns a GaussianCodeN whose .generator is the zero "
                           "vector; calling hermitian_dual() on it again tests orthogonality to 0.",
        }
        ex.save_json("results.json", out)
        ex.save_csv("exhaustive_decode_original.csv", rows)

        # PASS/FAIL bookkeeping (a failing paper claim is recorded, not hidden)
        for key, r in out["examples"].items():
            for w in r["worked_examples"]:
                if not (w["match_source"] and w["match_appendix"]):
                    ex.fail(f"{key}: worked example {w['example']} not reproduced")
            for nm, cnt in r.get("exhaustive_all_R", {}).items():
                if cnt["unique_wrong"] or cnt["non_unique"] or cnt["none_but_y_in_C2"]:
                    ex.fail(f"{key}/{nm}: exhaustive decode errors {cnt}")
        print_summary(out)


def print_summary(out):
    for key, r in out["examples"].items():
        print(f"\n== {key}: |C1|={r['orig_size_C1']} |C2|={r['orig_size_C2']} index={r['orig_index']} "
              f"nested={r['orig_nested']} sets_identical={r['sets_identical_C1'] and r['sets_identical_C2']}")
        for nm, e in r["eps"].items():
            ic = e["independent_check"]
            print(f"   eps[{nm}] = {e['elements']}  valid={ic['valid']}  orig_verify={e['orig_verify_epsilon_disjoint']}")
        for w in r["worked_examples"]:
            print(f"   {w['example']}: y={w['y']} -> e={w['source_decode_e']} c={w['source_decode_c']} "
                  f"(expected e={w['expected_e']}, c={w['expected_c']}) match={w['match_source']}/{w['match_appendix']}")
        for nm, cnt in r.get("exhaustive_all_R", {}).items():
            print(f"   exhaustive[{nm}]: {cnt}")
        s = r["orig_run_simulation_seeded"]
        print(f"   run_simulation(seeded): success {s['success']}/{s['trials']}, non_unique={s['non_unique']}")
    for d in out["dual_n2"]:
        print(f"   n=2 dual q={d['q']} gen={d['gen']}: orig={d['orig_dual_size']} indep={d['indep_dual_size']} "
              f"identical={d['identical']} ({d['orig_seconds']:.1f}s)")
    print("   double-dual probe:", out["double_dual_probe"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="phase1_original.toml")
    main(ap.parse_args().config)
