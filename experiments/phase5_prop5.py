"""Phase 5 - Proposition 5 under the Theorem 4 stabilizer, and physical recovery.

Three things are kept separate (as required):
  (1) classical coset identification            -> Phase 2 (decoder), restated here for eps
  (2) identification of a physical error by stabilizer measurement  -> sections A, B
  (3) recovery of the encoded quantum state      -> section C (alternative error set, LABELLED
      as an alternative design, not as a result of the paper)

Reproducible command:
    .venv/Scripts/python.exe experiments/phase5_prop5.py [--config phase5_prop5.toml] [--codes Z25]
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from epsqec.benchmarking import Experiment, load_config
from epsqec.css.build import build
from epsqec.stabilizer import lee_weight, min_weight_transversal


def random_logical(V, rng):
    c = rng.normal(size=len(V)) + 1j * rng.normal(size=len(V))
    c /= np.linalg.norm(c)
    return c @ V, c


def section_A(b, rng) -> dict:
    """Paper's reading: errors X(e), e in eps subset C2, detected by the Z-type stabilizers."""
    code, sp, R = b.code, b.space, b.ring
    out = {}
    # exhaustive over C2 and over R^n: kernel of the X-error syndrome map
    s_C2 = code.zsyn(b.C2.vectors())
    out["C2_elements_tested"] = int(b.C2.size)
    out["C2_elements_with_nonzero_syndrome"] = int(np.any(s_C2 != 0, axis=1).sum())
    s_all = code.zsyn(sp.vecs)
    ker = ~np.any(s_all != 0, axis=1)
    out["kernel_of_X_syndrome_equals_C2"] = bool(np.array_equal(ker, b.C2.mask))
    out["kernel_of_X_syndrome_equals_C1"] = bool(np.array_equal(ker, b.C1.mask))
    # eps: algebraic + state-level syndromes and the logical action
    V = code.logical_states(b.eps)
    psi, coef = random_logical(V, rng)
    rows = []
    for k, e in enumerate(b.eps):
        alg = tuple(int(x) for x in code.zsyn(e[None])[0])
        phi = sp.apply_X(e, psi)
        z_state, x_state = code.measure_state_syndrome(phi)
        L, leak = code.logical_matrix(V, lambda s, e=e: sp.apply_X(e, s))
        fid = float(abs(np.vdot(psi, phi)) ** 2)
        basis_overlap = float(abs(np.vdot(V[0], sp.apply_X(e, V[0]))) ** 2)
        rows.append({"e": R.fmt(e[0] if sp.n == 1 else e), "syndrome_algebraic": alg,
                     "syndrome_from_state_Z": z_state, "syndrome_from_state_X": x_state,
                     "stays_in_code_space_leak": leak, "acts_as_identity_on_code": bool(np.allclose(L, np.eye(len(V)))),
                     "fidelity_random_logical_state": fid, "|<psi_0|X(e)|psi_0>|^2": basis_overlap,
                     "e_in_C1": bool(b.C1.contains(e))})
    out["eps_rows"] = rows
    pats = {r["syndrome_from_state_Z"] + r["syndrome_from_state_X"] for r in rows}
    out["distinct_syndrome_patterns_over_eps"] = len(pats)
    out["|eps|"] = len(rows)
    out["prop5_holds_for_X_errors"] = len(pats) == len(rows)
    kl = code.knill_laflamme(V, [lambda s, e=e: sp.apply_X(e, s) for e in b.eps])
    out["knill_laflamme_eps_X_errors"] = kl
    return out


def section_B(b) -> dict:
    """Supplementary reading (NOT stated in the paper): errors Z(e), e in eps."""
    code, sp = b.code, b.space
    C1d = b.C1_dual
    s_all = code.xsyn(sp.vecs)
    ker = ~np.any(s_all != 0, axis=1)
    s_eps = code.xsyn(b.eps)
    keys = {tuple(r) for r in s_eps.tolist()}
    # is the Z-syndrome constant on the cosets C1 + e (what Prop. 5 would need)?
    const = True
    c1 = b.C1.vectors()
    for e in b.eps:
        s = code.xsyn(b.ring.add(c1, e[None]))
        if not np.all(s == s[0]):
            const = False
            break
    return {"kernel_of_Z_syndrome_equals_C1_dual": bool(np.array_equal(ker, C1d.mask)),
            "|C1_dual|": C1d.size, "C1_dual_subset_C1": C1d.issubset(b.C1),
            "distinct_Z_syndromes_over_eps": len(keys), "|eps|": len(b.eps),
            "Z_syndrome_constant_on_each_coset_C1+e": const}


def section_C(b, cfg, rng) -> dict:
    """ALTERNATIVE DESIGN (not the paper's result): correct X(a)Z(b) with a in T_X (transversal of
    R^n/C2) and b in T_Z (transversal of R^n/C1^perp), chosen with minimum Lee weight."""
    code, sp, R = b.code, b.space, b.ring
    C1d = b.C1_dual
    nX = sp.dim // b.C2.size
    nZ = sp.dim // C1d.size
    TX = min_weight_transversal(sp, code.zsyn_key, nX)
    TZ = min_weight_transversal(sp, code.xsyn_key, nZ)
    lutX = {int(k): a for k, a in zip(code.zsyn_key(TX), TX)}
    lutZ = {int(k): z for k, z in zip(code.xsyn_key(TZ), TZ)}
    V = code.logical_states(b.eps)
    psi, _ = random_logical(V, rng)
    q = R.q

    def key_of(t):
        return int(sum(int(v) * q ** j for j, v in enumerate(t)))

    def recover(phi):
        zs, xs = code.measure_state_syndrome(phi)
        a = lutX[key_of(zs)]
        z = lutZ[key_of(xs)]
        return sp.apply_X(R.neg(a), sp.apply_Z(R.neg(z), phi)), zs, xs

    pairs = [(i, j) for i in range(len(TX)) for j in range(len(TZ))]
    mode = "exhaustive"
    large = sp.dim > cfg["large_dim"]
    n_s = cfg["large_dim_sampled_pairs"] if large else cfg["sampled_pairs"]
    if len(pairs) > cfg["exhaustive_pairs_limit"] or large:
        sel = rng.choice(len(pairs), n_s, replace=False)
        pairs = [pairs[s] for s in sel]
        mode = f"sampled {n_s}"
    ok = 0
    worst = 1.0
    t0 = time.perf_counter()
    for i, j in pairs:
        phi = sp.apply_X(TX[i], sp.apply_Z(TZ[j], psi))
        rec, _, _ = recover(phi)
        f = float(abs(np.vdot(psi, rec)) ** 2)
        worst = min(worst, f)
        ok += f > 1 - 1e-9
    dt = time.perf_counter() - t0
    # contrast: Lee-weight-2 X errors that are not in T_X
    w = lee_weight(R, sp.vecs)
    cand = sp.vecs[w == 2]
    if len(cand) > cfg["weight2_samples"]:
        cand = cand[rng.choice(len(cand), cfg["weight2_samples"], replace=False)]
    ok2 = 0
    for a in cand:
        rec, _, _ = recover(sp.apply_X(a, psi))
        ok2 += abs(np.vdot(psi, rec)) ** 2 > 1 - 1e-9
    res = {"label": "ALTERNATIVE DESIGN - not a result of the paper",
           "|T_X|": len(TX), "|T_Z|": len(TZ), "T_X": [R.fmt(t[0] if sp.n == 1 else t) for t in TX[:20]],
           "max_lee_weight_T_X": int(lee_weight(R, TX).max()), "max_lee_weight_T_Z": int(lee_weight(R, TZ).max()),
           "pairs_tested": len(pairs), "mode": mode, "recovered_exactly": int(ok), "min_fidelity": worst,
           "seconds": dt, "weight2_X_errors_tested": len(cand), "weight2_X_errors_recovered": int(ok2)}
    # Knill-Laflamme for E = {X(a) Z(b)}
    E = [(a, z) for a in TX for z in TZ]
    ops = None
    if len(E) <= cfg["kl_exhaustive_limit"]:
        ops = [lambda s, a=a, z=z: sp.apply_X(a, sp.apply_Z(z, s)) for a, z in E]
        res["knill_laflamme_alt_set"] = code.knill_laflamme(V, ops)
    else:
        worst_dev = 0.0
        K = len(V)
        n_kl = cfg["large_dim_kl_pairs"] if sp.dim > cfg["large_dim"] else cfg["kl_sampled_pairs"]
        for _ in range(n_kl):
            (a1, z1), (a2, z2) = E[rng.integers(len(E))], E[rng.integers(len(E))]
            W1 = np.stack([sp.apply_X(a1, sp.apply_Z(z1, v)) for v in V])
            W2 = np.stack([sp.apply_X(a2, sp.apply_Z(z2, v)) for v in V])
            M = W1.conj() @ W2.T
            worst_dev = max(worst_dev, float(np.linalg.norm(M - np.trace(M) / K * np.eye(K))))
        res["knill_laflamme_alt_set"] = {"max_deviation": worst_dev, "mode": f"sampled {n_kl} pairs"}
    return res


def main(cfg_path, only):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    with Experiment("quantum", "phase5_prop5", cfg, seed=cfg["seed"]) as ex:
        out = {}
        for spec in cfg["codes"]:
            if only and spec["key"] not in only:
                continue
            t0 = time.perf_counter()
            b = build(spec)
            r = {"dim_H": b.space.dim, "K": b.code.K_formula}
            r["A_paper_reading_X_errors"] = section_A(b, rng)
            r["B_supplementary_Z_errors"] = section_B(b)
            r["C_alternative_design_recovery"] = section_C(b, cfg, rng)
            r["seconds"] = time.perf_counter() - t0
            out[spec["key"]] = r
            A, B, C = r["A_paper_reading_X_errors"], r["B_supplementary_Z_errors"], r["C_alternative_design_recovery"]
            print(f"== {spec['key']} dim={b.space.dim} K={b.code.K_formula}")
            print("  A:", {k: A[k] for k in ("C2_elements_with_nonzero_syndrome", "kernel_of_X_syndrome_equals_C2",
                                            "distinct_syndrome_patterns_over_eps", "|eps|", "prop5_holds_for_X_errors")},
                  "KL dev", round(A["knill_laflamme_eps_X_errors"]["max_deviation"], 4))
            for row in A["eps_rows"][:3]:
                print("     ", {k: row[k] for k in ("e", "syndrome_from_state_Z", "syndrome_from_state_X",
                                                    "acts_as_identity_on_code", "fidelity_random_logical_state", "|<psi_0|X(e)|psi_0>|^2")})
            print("  B:", B)
            print("  C:", {k: C[k] for k in ("|T_X|", "|T_Z|", "T_X", "pairs_tested", "recovered_exactly", "min_fidelity",
                                            "weight2_X_errors_tested", "weight2_X_errors_recovered")},
                  "KL", C["knill_laflamme_alt_set"])
            # bookkeeping: the paper's claim is TESTED; its failure is a result, recorded as such
            if not A["prop5_holds_for_X_errors"]:
                ex.note(f"{spec['key']}: Proposition 5 refuted for X-type errors "
                        f"({A['distinct_syndrome_patterns_over_eps']} syndrome pattern(s) for |eps|={A['|eps|']})")
            if C["recovered_exactly"] != C["pairs_tested"]:
                ex.fail(f"{spec['key']}: alternative-design recovery failed on some correctable errors")
        ex.save_json("results.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="phase5_prop5.toml")
    ap.add_argument("--codes", default=None)
    a = ap.parse_args()
    main(a.config, set(a.codes.split(",")) if a.codes else None)
