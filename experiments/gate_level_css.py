"""Gate-level CSS simulation of the ring codes in PennyLane (layouts A and B), gated test sequence.

    .venv/Scripts/python.exe experiments/gate_level_css.py [--config gate_level_css.toml] [--codes Z25,Z65]

Test order (a step runs only if all previous steps of that code PASSed; otherwise NOT RUN):
  1  math:    commutation, K = |C2|/|C1|, orthonormal logical states, closed-form dual (matrix-free)
  2  encoder: gate-level split-template encoder (layout B) vs |C1|^{-1/2} sum_{c in C1} |c + t_j>
  3  cycle:   encode -> X(a)Z(b) -> sequential syndromes (mid-circuit measurement, tree-traversal)
              -> conditional recovery -> decode; fidelity for (a,b) in T_X x T_Z, both orders,
              basis inputs and random superpositions (round trip: P(L = 0, data = 0) = fidelity)
  4  negative control: X(e), e in eps \ {0}: zero syndrome and <psi_0|X(e)|psi_0> = 0
  5  Z(e), e in eps: number of distinct X-type syndromes vs (eps - eps) /\ C1^perpH = {0}
Layout A (binary a, b registers, qml.Adder) runs steps 3-5 with the input/output loaded by a
gate-level Mottonen preparation of the reference code state (no gate-level encoder exists for A).
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pennylane as qml

from epsqec.benchmarking import Experiment, load_config
from epsqec.css.build import build
from epsqec.ideals import hermitian_dual, hermitian_dual_closed_form
from epsqec.pl_circuits.cycle import LayoutA, LayoutB, cycle_program, run_native, run_segmented
from epsqec.pl_circuits.split_layout import SplitCircuits

TOL = 1e-12


# ============================================================================ helpers
def random_amps(rng, K):
    a = rng.normal(size=K) + 1j * rng.normal(size=K)
    return a / np.linalg.norm(a)


def dev_for(cfg, n):
    return qml.device(cfg["device"], wires=n)


# ============================================================================ steps
def step1_math(b) -> dict:
    code = b.code
    V = code.logical_states(b.eps)
    cf = hermitian_dual_closed_form(b.ring, b.C2_gen) if b.C2_gen is not None else None
    r = {
        "noncommuting_pairs": code.commutation_exhaustive()["noncommuting_pairs"],
        "K_formula": b.C2.size // b.C1.size,
        "dim_structural": code.dim_structural(),
        "dim_trace_formula": code.dim_trace_formula(),
        "gram_minus_I": float(np.abs(V.conj() @ V.T - np.eye(len(V))).max()),
        "closed_form_dual_equals_enumerated": (cf == hermitian_dual(b.C2)) if cf is not None else None,
        "C2perp_subset_C1": b.D_true.issubset(b.C1),
    }
    r["PASS"] = (r["noncommuting_pairs"] == 0 and r["dim_structural"] == r["K_formula"]
                 and abs(r["dim_trace_formula"] - r["K_formula"]) < 1e-9 and r["gram_minus_I"] < 1e-12
                 and r["closed_form_dual_equals_enumerated"] is not False)
    return r


def step2_encoder(b, cfg, rng) -> dict:
    sc = SplitCircuits(b, reuse_ancilla=True)
    lay = sc.L
    dev = dev_for(cfg, sc.n_wires)
    rows, worst, rest_max, leak_max = [], 1.0, 0.0, 0.0
    valid = lay.valid_mask()
    for j in range(sc.K):
        @qml.qnode(dev)
        def enc():
            sc.prepare_basis(j)
            sc.encode()
            return qml.state()

        st = np.asarray(enc()).reshape(2 ** lay.n_qubits, -1)
        rest = float(np.abs(st[:, 1:]).max()) if st.shape[1] > 1 else 0.0
        t = sc.canonical_t(j)
        ref = lay.embed(b.code.logical_states(np.asarray(t).reshape(1, 1, 2))[0])
        fid = float(abs(np.vdot(ref, st[:, 0])) ** 2)
        leak = float(np.sum(np.abs(st[~valid, 0]) ** 2))
        worst, rest_max, leak_max = min(worst, fid), max(rest_max, rest), max(leak_max, leak)
        rows.append({"j": j, "t_j": b.ring.fmt(t), "fidelity": fid, "logical_and_ancilla_residual": rest, "leakage": leak})
    # linearity: random superposition
    amps = random_amps(rng, sc.K)

    @qml.qnode(dev)
    def enc_sup():
        sc.prepare_logical(amps)
        sc.encode()
        return qml.state()

    st = np.asarray(enc_sup()).reshape(2 ** lay.n_qubits, -1)
    T = np.array([sc.canonical_t(j) for j in range(sc.K)]).reshape(-1, 1, 2)
    ref = lay.embed(amps @ b.code.logical_states(T))
    sup_fid = float(abs(np.vdot(ref, st[:, 0])) ** 2)
    # relation between canonical labels and the paper's eps (which canonical j has the same coset)
    rel = []
    for e in b.eps:
        for j in range(sc.K):
            if b.C1.contains(b.ring.sub(e.reshape(2), sc.canonical_t(j).reshape(2))):
                rel.append({"eps": b.ring.fmt(e.reshape(2)), "canonical_j": j})
    return {"rows": rows, "worst_fidelity": worst, "superposition_fidelity": sup_fid,
            "max_residual_logical_ancilla": rest_max, "max_leakage": leak_max, "eps_to_canonical": rel,
            "wires": sc.wire_summary(), "PASS": worst >= 1 - TOL and sup_fid >= 1 - TOL and rest_max < 1e-9}


def cycle_runs(layout, cfg, pairs, inputs, order, engine) -> list[dict]:
    out = []
    for (a, f), inp in zip(pairs, inputs):
        prog = cycle_program(layout, a, f, inp, order)
        t = time.perf_counter()
        if engine == "native":
            p = run_native(prog, layout.n_wires, layout.out_wires(), device=cfg["native_device"],
                           mcm_method=cfg["mcm_method"])
            info = {}
        else:
            p, info = run_segmented(prog, layout.n_wires, layout.out_wires(), device=cfg["device"],
                                    branch_tol=cfg["branch_tol"])
        out.append({"a": layout.b.ring.fmt(a), "b": layout.b.ring.fmt(f), "order": order, "engine": engine,
                    "input": "basis %d" % inp if isinstance(inp, (int, np.integer)) else "random superposition",
                    "fidelity": float(p[0]), "seconds": time.perf_counter() - t,
                    "records": info.get("records"), "discarded_probability": info.get("discarded_probability")})
    return out


def step3_cycle(b, cfg, rng, layout_name, reuse, log) -> dict:
    L = LayoutB(b, reuse) if layout_name == "B" else LayoutA(b, reuse)
    allpairs = [(a, f) for a in L.TX for f in L.TZ]
    lim = cfg["cycle_exhaustive_limit"]
    if layout_name == "B" and not reuse:
        lim = 0  # separate-register variant: sampled (it only checks the reset-free bookkeeping)
    if len(allpairs) <= lim:
        pairs, mode = allpairs, "exhaustive"
    else:
        n = min(cfg["cycle_sample"], len(allpairs))
        sel = rng.choice(len(allpairs), n, replace=False)
        pairs, mode = [allpairs[i] for i in sel], f"sampled {n} of {len(allpairs)}"
    rows = []
    for order in cfg["orders"]:
        rows += cycle_runs(L, cfg, pairs, [i % L.K for i in range(len(pairs))], order, cfg["engine"])
        log(f"   {b.key}/{layout_name}{'/reuse' if reuse else ''} {order} basis ({len(pairs)}): "
            f"min F = {min(r['fidelity'] for r in rows if r['order'] == order):.13f}")
        nsup = min(len(pairs), cfg["superposition_pairs"])
        idx = rng.choice(len(pairs), nsup, replace=False)
        sup = cycle_runs(L, cfg, [pairs[i] for i in idx], [random_amps(rng, L.K) for _ in idx], order, cfg["engine"])
        rows += sup
        log(f"   {b.key}/{layout_name} {order} superpositions ({nsup}): min F = {min(r['fidelity'] for r in sup):.13f}")
    xc = []
    if cfg.get("native_crosscheck", 0) and layout_name == "B" and cfg["engine"] != "native":
        idx = rng.choice(len(pairs), min(len(pairs), cfg["native_crosscheck"]), replace=False)
        for n_, i in enumerate(idx):
            order = cfg["orders"][n_ % len(cfg["orders"])]
            amps = random_amps(rng, L.K)
            prog = cycle_program(L, pairs[i][0], pairs[i][1], amps, order)
            ps, _ = run_segmented(prog, L.n_wires, L.out_wires(), device=cfg["device"], branch_tol=cfg["branch_tol"])
            t = time.perf_counter()
            pn = run_native(prog, L.n_wires, L.out_wires(), device=cfg["native_device"], mcm_method=cfg["mcm_method"])
            xc.append({"a": b.ring.fmt(pairs[i][0]), "b": b.ring.fmt(pairs[i][1]), "order": order,
                       "segmented_P0": float(ps[0]), "native_P0": float(pn[0]),
                       "max_abs_diff_full_distribution": float(np.abs(ps - pn).max()),
                       "native_seconds": time.perf_counter() - t})
        log(f"   native cross-check ({len(xc)} runs): max |diff| = {max(r['max_abs_diff_full_distribution'] for r in xc):.2e}")
    fids = [r["fidelity"] for r in rows]
    ok = min(fids) >= 1 - cfg["fidelity_tol"] and all(r["max_abs_diff_full_distribution"] < 1e-10 for r in xc)
    return {"layout": layout_name, "reuse_ancilla": reuse, "wires": L.n_wires, "pairs_mode": mode,
            "n_pairs": len(pairs), "|T_X|": len(L.TX), "|T_Z|": len(L.TZ), "runs": len(rows),
            "min_fidelity": min(fids), "n_fidelity_1": int(sum(f >= 1 - cfg["fidelity_tol"] for f in fids)),
            "max_discarded_probability": max((r["discarded_probability"] or 0.0) for r in rows),
            "mean_seconds": float(np.mean([r["seconds"] for r in rows])), "native_crosscheck": xc,
            "rows": rows, "PASS": ok}


def part_value_from_index(sc, P, idx: int) -> int:
    """Index of the probs over the part's ancilla wires (digit order P.digits) -> measured value."""
    bits = format(idx, f"0{sum(d.m for d in P.digits)}b")
    pos, reg = 0, {}
    for d in P.digits:
        reg[d.name] = int(bits[pos:pos + d.m], 2)
        pos += d.m
    val = 0
    for d in sc.measured_value_order(P):
        val = val * d.p + reg[d.name]
    return val


def measure_parts_coherently(sc, dev, prefix, parts):
    """One circuit per syndrome part on the shared ancilla pool (no mid-circuit measurement):
    returns [(value, probability)] with value read exactly as in the cycle."""
    out = []
    for P in parts:
        ext = sc.z_syndrome if P.kind == "Z" else sc.x_syndrome

        @qml.qnode(dev)
        def syn():
            prefix()
            ext(P)
            return qml.probs(wires=[w for d in P.digits for w in d.wires])

        pr = np.asarray(syn())
        idx = int(np.argmax(pr))
        out.append((part_value_from_index(sc, P, idx), float(pr[idx])))
    return out


def step4_negative(b, cfg) -> dict:
    sc = SplitCircuits(b, reuse_ancilla=True)
    dev = dev_for(cfg, sc.n_wires)
    R = b.ring
    rows = []
    for e in b.eps[1:]:
        e = e.reshape(2)

        def prefix(e=e):
            sc.prepare_basis(0)
            sc.encode()
            sc.X(e)

        meas = measure_parts_coherently(sc, dev, prefix, sc.parts)

        @qml.qnode(dev)
        def overlap():
            prefix()
            sc.decode()
            return qml.probs(wires=sc.logical_wires + sc.data_wires)

        ov = float(np.asarray(overlap())[0])
        rows.append({"e": R.fmt(e), "syndrome_values_Z_then_X": [v for v, _ in meas],
                     "syndrome_probability": min(pv for _, pv in meas),
                     "all_syndromes_zero": all(v == 0 for v, _ in meas), "|<psi0|X(e)|psi0>|^2": ov,
                     "e_in_C1": bool(b.C1.contains(e))})
    ok = all(r["all_syndromes_zero"] and r["syndrome_probability"] > 1 - 1e-9 and r["|<psi0|X(e)|psi0>|^2"] < 1e-12
             for r in rows)
    return {"rows": rows, "reproduces_prop5_counterexample": ok, "PASS": ok}


def step5_zreading(b, cfg) -> dict:
    sc = SplitCircuits(b, reuse_ancilla=True)
    dev = dev_for(cfg, sc.n_wires)
    R = b.ring
    xparts = [P for P in sc.parts if P.kind == "X"]
    rows = []
    for e in b.eps:
        e = e.reshape(2)

        def prefix(e=e):
            sc.prepare_basis(0)
            sc.encode()
            sc.Z(e)

        meas = measure_parts_coherently(sc, dev, prefix, xparts)
        rows.append({"e": R.fmt(e), "measured": tuple(v for v, _ in meas),
                     "expected": tuple(sc.expected_part(P, e) for P in xparts),
                     "probability": min(pv for _, pv in meas)})
    D1 = b.C1_dual
    diffs = R.sub(b.eps[:, None, 0, :], b.eps[None, :, 0, :]).reshape(-1, 1, 2)
    nz = ~np.all(diffs.reshape(-1, 2) == 0, axis=1)
    cond = not bool(D1.contains(diffs[nz]).any())
    distinct = len({r["measured"] for r in rows})
    ok_meas = all(r["measured"] == r["expected"] and r["probability"] > 1 - 1e-9 for r in rows)
    return {"rows": rows, "distinct_syndromes": distinct, "|eps|": len(rows),
            "condition_(eps-eps)_cap_C1perp_trivial": cond,
            "equivalence_holds": cond == (distinct == len(rows)), "measured_equals_expected": ok_meas,
            "PASS": ok_meas and cond == (distinct == len(rows))}


# ============================================================================ main
def main(cfg_path, only):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    with Experiment("quantum", cfg.get("experiment_name", "gate_level_css"), cfg, seed=cfg["seed"]) as ex:
        out = {"pennylane": qml.__version__, "device": cfg["device"], "mcm_method": cfg["mcm_method"],
               "trace_convention": cfg.get("trace_convention", "paper"), "codes": {}}

        def log(s):
            print(s, flush=True)

        for spec in cfg["codes"]:
            if only and spec["key"] not in only:
                continue
            spec = {**spec, "trace_convention": cfg.get("trace_convention", "paper")}
            b = build(spec)
            b.C2_gen = spec.get("alpha2", None)
            if b.C2_gen is None:
                from epsqec.css import PAPER_EXAMPLES

                pe = PAPER_EXAMPLES.get(spec["key"])
                b.C2_gen = pe.alpha2 if pe else None
            res = {"steps": {}}
            failed = None

            def run(name, fn):
                nonlocal failed
                if failed:
                    res["steps"][name] = {"status": "NOT RUN", "reason": f"previous step '{failed}' did not pass"}
                    log(f"[{spec['key']}] {name}: NOT RUN")
                    return
                t = time.perf_counter()
                try:
                    r = fn()
                    r["status"] = "PASS" if r.pop("PASS") else "FAIL"
                except Exception as exc:  # recorded, never hidden
                    r = {"status": "ERROR", "error": repr(exc)[:500]}
                r["seconds"] = time.perf_counter() - t
                res["steps"][name] = r
                log(f"[{spec['key']}] {name}: {r['status']} ({r['seconds']:.1f} s)")
                if r["status"] != "PASS":
                    failed = name
                    ex.fail(f"{spec['key']}: step {name} {r['status']}")
                ex.save_json("results_partial.json", out)

            out["codes"][spec["key"]] = res
            ccfg = {**cfg, **spec.get("overrides", {})}
            res["config_used"] = {k: ccfg[k] for k in ("device", "engine", "native_crosscheck", "cycle_sample",
                                                        "superposition_pairs", "cycle_exhaustive_limit")}
            run("1_math", lambda: step1_math(b))
            run("2_encoder_B", lambda: step2_encoder(b, ccfg, rng))
            for lay in spec.get("layouts", ["B"]):
                for reuse in (spec.get("reuse", [True]) if lay == "B" else [False]):
                    lcfg = dict(ccfg)
                    if lay == "B" and not reuse:
                        lcfg["native_crosscheck"] = ccfg.get("native_crosscheck_noreuse", 1)
                    run(f"3_cycle_{lay}{'_reuse' if reuse else ''}",
                        lambda lay=lay, reuse=reuse, lcfg=lcfg: step3_cycle(b, lcfg, rng, lay, reuse, log))
            run("4_negative_control_B", lambda: step4_negative(b, ccfg))
            run("5_Z_reading_B", lambda: step5_zreading(b, ccfg))
        ex.save_json("results.json", out)
        rows = []
        for key, res in out["codes"].items():
            for name, r in res["steps"].items():
                for row in r.get("rows", []) if name.startswith("3_") else []:
                    rows.append({"code": key, "step": name, **row})
        ex.save_csv("cycle_runs.csv", rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="gate_level_css.toml")
    ap.add_argument("--codes", default=None)
    a = ap.parse_args()
    main(a.config, set(a.codes.split(",")) if a.codes else None)
