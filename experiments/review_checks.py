"""Review checks (second-author report): A1 closed-form dual, Definition-6 coincidences, A3 printed
conditions, A4 Z_9 hypothesis, B4 additive (non-module) codes, C2 trace convention.

    .venv/Scripts/python.exe experiments/review_checks.py [--config review_checks.toml]
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from epsqec.benchmarking import Experiment, load_config
from epsqec.css import PAPER_EXAMPLES
from epsqec.css.build import build
from epsqec.ideals import (AdditiveCode, hermitian_dual, hermitian_dual_closed_form, hermitian_dual_def6,
                           trace_dual)
from epsqec.ring import GaussianRing, factorize, zi
from epsqec.stabilizer import QuditSpace, RingCSSCode, min_weight_transversal


def divisor_generators(q):
    primes = []
    for p, e in factorize(q).items():
        pi = zi.gaussian_prime_above(p)
        primes.append((pi, zi.conj(pi), e))
    divs = [(1, 0)]
    for pi, pib, e in primes:
        new = []
        for d in divs:
            for i in range(e + 1):
                for j in range(e + 1):
                    x = d
                    for _ in range(i):
                        x = zi.mul(x, pi)
                    for _ in range(j):
                        x = zi.mul(x, pib)
                    new.append(x)
        divs = new
    return divs


def a1_closed_form(q, n_random, rng) -> dict:
    R = GaussianRing(q)
    gens = divisor_generators(q)
    ideals = {}
    for d in gens:
        C = AdditiveCode.principal(R, d)
        ideals.setdefault(C.mask.tobytes(), (d, C))
    rows, mism = [], 0
    for d, C in ideals.values():
        D = hermitian_dual(C)
        cf = hermitian_dual_closed_form(R, d)
        d6 = hermitian_dual_def6(R, d)
        ok = cf == D
        mism += not ok
        rows.append({"q": q, "generator": f"{d[0]}+{d[1]}i", "|C|": C.size, "|C^perpH|": D.size,
                     "closed_form_equals_annihilator": ok, "def6_equals_true_dual": d6 == D,
                     "Ann(alpha)_equals_<alpha>": AdditiveCode.from_indices(
                         R, 1, R.index(R.conj(D.vectors()[:, 0, :]))) == C})
    # random generators (not divisors): closed form must still match
    rnd_mism = 0
    E = R.elements()
    for x in E[rng.integers(0, len(E), n_random)]:
        C = AdditiveCode.principal(R, x)
        rnd_mism += not (hermitian_dual_closed_form(R, x) == hermitian_dual(C))
    coincide = [r["generator"] for r in rows if r["def6_equals_true_dual"]]
    return {"q": q, "n_ideals": len(rows), "closed_form_mismatches_all_ideals": mism,
            "random_generators_tested": n_random, "closed_form_mismatches_random": rnd_mism,
            "def6_coincides_with_true_dual_for": coincide, "rows": rows}


def example_generators() -> list[dict]:
    specs = {"Z25": PAPER_EXAMPLES["Z25"], "Z85": PAPER_EXAMPLES["Z85"], "Z325": PAPER_EXAMPLES["Z325"]}
    out = []
    for key, pe in specs.items():
        R = GaussianRing(pe.q)
        for role, a in (("alpha1 (C1)", pe.alpha1), ("alpha2 (C2)", pe.alpha2)):
            C = AdditiveCode.principal(R, a)
            D = hermitian_dual(C)
            out.append({"example": key, "role": role, "alpha": f"{a[0]}+{a[1]}i", "|C|": C.size,
                        "|true dual|": D.size, "|<sigma(alpha)>|": hermitian_dual_def6(R, a).size,
                        "def6_equals_true_dual": hermitian_dual_def6(R, a) == D})
    return out


def a3_printed_conditions() -> list[dict]:
    """Examples 6/7 print  C2^perpH = {z : z * conj(alpha2) = 0 (mod q)}  (bar visible in the PDF)."""
    out = []
    for key, q, a2, dual_gen in (("Example 7 (Z25)", 25, (2, 1), (10, 5)), ("Example 6 (Z325)", 325, (3, 2), (75, 50))):
        R = GaussianRing(q)
        C2 = AdditiveCode.principal(R, a2)
        E = R.elements()
        printed = AdditiveCode.from_indices(R, 1, R.index(E[R.is_zero(R.mul(E, R.conj(R.elem(*a2))))]))
        without_bar = AdditiveCode.from_indices(R, 1, R.index(E[R.is_zero(R.mul(E, R.elem(*a2)))]))
        g = R.elem(*dual_gen)
        out.append({"example": key, "printed_condition": "z * conj(alpha2) = 0 (mod q)",
                    "printed_set_equals_true_dual": printed == hermitian_dual(C2),
                    "set_without_bar_equals_true_dual": without_bar == hermitian_dual(C2),
                    "dual_generator": R.fmt(g),
                    "gen*conj(alpha2)": R.fmt(R.mul(g, R.conj(R.elem(*a2)))),
                    "gen*alpha2": R.fmt(R.mul(g, R.elem(*a2)))})
    return out


def b4_additive(cfg) -> dict:
    q = cfg["q"]
    R = GaussianRing(q)
    C = AdditiveCode.zq_span(R, 1, [np.array(cfg["C"])])
    DH, DT, DTr = hermitian_dual(C), trace_dual(C, "left"), trace_dual(C, "right")
    C1 = AdditiveCode.zq_span(R, 1, [np.array([g]) for g in cfg["C1"]])
    C2 = AdditiveCode.zq_span(R, 1, [np.array([g]) for g in cfg["C2"]])
    sp = QuditSpace(R, 1)
    res = {"C": "Z_q * 1", "|C|": C.size, "C_is_R_module": C.is_R_module(), "|C^perpH|": DH.size,
           "|C^perpTr| (left)": DT.size, "|C^perpTr| (right)": DTr.size,
           "|C||C^perpH|": C.size * DH.size, "|C||C^perpTr|": C.size * DT.size,
           "|R|": R.size, "pair": {"|C1|": C1.size, "|C2|": C2.size, "C1_subset_C2": C1.issubset(C2),
                                   "C1_is_R_module": C1.is_R_module(), "C2_is_R_module": C2.is_R_module(),
                                   "K=|C2|/|C1|": C2.size // C1.size}}
    for tag, D in (("hermitian_dual", hermitian_dual(C2)), ("trace_dual_left", trace_dual(C2, "left")),
                   ("trace_dual_right", trace_dual(C2, "right"))):
        code = RingCSSCode(sp, C1, C2, D, tag)
        res["pair"][tag] = {"|D|": D.size, "noncommuting_pairs": code.commutation_exhaustive()["noncommuting_pairs"],
                            "code_dimension": code.dim_structural(), "dense_nullspace": code.dim_nullspace_dense()}
    return res


def c2_conventions(keys) -> list[dict]:
    out = []
    for key in keys:
        for conv in ("paper", "2re"):
            b = build({"key": key, "trace_convention": conv})
            code, sp, R = b.code, b.space, b.ring
            rng = np.random.default_rng(0)
            psi = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
            worst = 0.0
            for _ in range(40):
                u, v = sp.vecs[rng.integers(sp.dim, size=2)]
                lhs = sp.apply_Z(v, sp.apply_X(u, psi))
                rhs = sp.chi_pair(v, u) * sp.apply_X(u, sp.apply_Z(v, psi))
                worst = max(worst, float(np.abs(lhs - rhs).max()))
            zs = code.zsyn(b.C2.vectors())
            xs_eps = {tuple(r) for r in code.xsyn(b.eps).tolist()}
            TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // b.C2.size)
            TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // b.C1_dual.size)
            out.append({"code": key, "trace_convention": conv, "pauli_relation_max_error": worst,
                        "trace_dual_equals_hermitian_dual": trace_dual(b.C2) == b.D_true,
                        "noncommuting_pairs": code.commutation_exhaustive()["noncommuting_pairs"],
                        "K_structural": code.dim_structural(), "K_formula": b.C2.size // b.C1.size,
                        "X_reading_C2_nonzero_syndromes": int(np.any(zs != 0, axis=1).sum()),
                        "Z_reading_distinct_over_eps": len(xs_eps), "|eps|": len(b.eps),
                        "|T_X|": len(TX), "|T_Z|": len(TZ)})
    return out


def main(cfg_path):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    with Experiment("algebra", "review_checks", cfg, seed=cfg["seed"]) as ex:
        out = {}
        t = time.perf_counter()
        out["A1_closed_form"] = [a1_closed_form(q, cfg["random_alpha_per_q"], rng) for q in cfg["closed_form_q"]]
        for r in out["A1_closed_form"]:
            print("A1", r["q"], {k: r[k] for k in ("n_ideals", "closed_form_mismatches_all_ideals",
                                                  "closed_form_mismatches_random", "def6_coincides_with_true_dual_for")})
            if r["closed_form_mismatches_all_ideals"] or r["closed_form_mismatches_random"]:
                ex.fail(f"closed form mismatch for q={r['q']}")
        out["A1_example_generators"] = example_generators()
        for r in out["A1_example_generators"]:
            print("A1-ex", r)
        out["A3_printed_conditions"] = a3_printed_conditions()
        for r in out["A3_printed_conditions"]:
            print("A3", r)
        out["A4_Z9"] = {"q": 9, "prime_divisors": list(factorize(9)), "3 mod 4": 3 % 4,
                        "inside_paper_hypothesis": all(p % 4 == 1 for p in factorize(9))}
        out["B4_additive"] = b4_additive(cfg["additive_counterexample"])
        print("B4", out["B4_additive"])
        out["C2_conventions"] = c2_conventions(cfg["convention_check_codes"])
        for r in out["C2_conventions"]:
            print("C2", r)
        ex.save_json("results.json", out)
        ex.save_csv("closed_form_all_ideals.csv", [row for r in out["A1_closed_form"] for row in r["rows"]])
        print("seconds", time.perf_counter() - t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="review_checks.toml")
    main(ap.parse_args().config)
