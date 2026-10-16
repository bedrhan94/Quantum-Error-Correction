"""Phase 4 - generalised Pauli operators, stabilizer group and code space (numerical, matrix-free).

Reproducible command:
    .venv/Scripts/python.exe experiments/phase4_stabilizer.py [--config phase4_stabilizer.toml] [--codes Z25,Z85]
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from epsqec.benchmarking import Experiment, load_config
from epsqec.css.build import build


def unitarity(b, rng, sampled=200) -> dict:
    sp, R = b.space, b.ring
    dim = sp.dim
    if dim <= 7225:
        U = sp.vecs
        mode = "all u in R^n"
    else:
        U = np.concatenate([np.array(b.code.xgens + b.code.zgens), sp.vecs[rng.integers(0, dim, sampled)]])
        mode = f"generators + {sampled} random"
    perm_ok = True
    for u in U:
        g = sp.gather_X(u)
        if len(np.unique(g)) != dim:
            perm_ok = False
            break
    phase_ok = all(np.allclose(np.abs(sp.z_phase(v)), 1) for v in U[: min(len(U), 400)])
    out = {"X_is_permutation": perm_ok, "Z_unit_modulus": phase_ok, "mode": mode, "n_tested": len(U)}
    if dim <= 625:
        I = np.eye(dim)
        dev = 0.0
        for u in U[:: max(1, len(U) // 50)]:
            X = sp.sparse_X(u)
            Z = sp.sparse_Z(u)
            dev = max(dev, abs(X.conj().T @ X - I).max(), abs(Z.conj().T @ Z - I).max())
        out["sparse_UdagU_minus_I_max"] = float(dev)
    return out


def pauli_relations(b, rng, exhaustive_limit, n_pairs) -> dict:
    sp, R = b.space, b.ring
    dim = sp.dim
    psi = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    psi /= np.linalg.norm(psi)
    worst = 0.0
    if dim ** 3 <= exhaustive_limit:
        mode = "exhaustive over all (u, v) in R^n x R^n"
        Zall = np.stack([sp.z_phase(v) for v in sp.vecs])  # (dim, dim): row v
        for u in sp.vecs:
            g = sp.gather_X(u)
            lhs = Zall * psi[g][None, :]  # Z(v) X(u) psi for all v
            rhs = (Zall * psi[None, :])[:, g]  # X(u) Z(v) psi for all v
            chi = np.exp(2j * np.pi * R.trace(R.hermitian(sp.vecs, u[None])) / R.q)  # chi(<v,u>) per v
            worst = max(worst, float(np.abs(lhs - chi[:, None] * rhs).max()))
        n = dim * dim
    else:
        mode = f"{n_pairs} random (u, v) pairs"
        for _ in range(n_pairs):
            u = sp.vecs[rng.integers(dim)]
            v = sp.vecs[rng.integers(dim)]
            lhs = sp.apply_Z(v, sp.apply_X(u, psi))
            rhs = sp.chi_pair(v, u) * sp.apply_X(u, sp.apply_Z(v, psi))
            worst = max(worst, float(np.abs(lhs - rhs).max()))
        n = n_pairs
    # group laws on random pairs
    law = 0.0
    for _ in range(50):
        u, u2, v, v2 = sp.vecs[rng.integers(dim, size=4)]
        law = max(law, float(np.abs(sp.apply_X(u, sp.apply_X(u2, psi)) - sp.apply_X(R.add(u, u2), psi)).max()))
        law = max(law, float(np.abs(sp.apply_Z(v, sp.apply_Z(v2, psi)) - sp.apply_Z(R.add(v, v2), psi)).max()))
    # order of X(u) equals additive order of u (generators)
    orders = []
    for u in b.code.xgens:
        k, w = 1, R.reduce(u)
        while not R.is_zero(w).all():
            w = R.add(w, u)
            k += 1
        phi = psi.copy()
        for _ in range(k):
            phi = sp.apply_X(u, phi)
        orders.append({"u": R.fmt(u), "additive_order": k, "X(u)^order_is_I": bool(np.allclose(phi, psi))})
    return {"commutation_relation_max_error": worst, "mode": mode, "pairs": n,
            "group_law_max_error": law, "x_generator_orders": orders}


def group_order(code, rng, n_coord=32) -> dict:
    """Count distinct operators X(u)Z(v), u in C1, v in D, by fingerprints on random coordinates."""
    sp, R = code.space, code.ring
    r = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
    xs = rng.integers(0, sp.dim, n_coord)
    Xs = sp.vecs[xs]
    U, Vv = code.C1.vectors(), code.Zg.vectors()
    prints = set()
    scalar_hits = 0
    for v in Vv:
        ph = np.exp(2j * np.pi * R.trace(R.hermitian(v[None], sp.vecs)) / R.q)
        zr = ph * r
        for u in U:
            idx = R.vec_index(R.sub(Xs, u[None]))  # (X(u) Z(v) r)[x] = (Z(v) r)[x - u]
            val = zr[idx]
            prints.add(tuple(np.round(val, 8)))
            if np.allclose(val, (val[0] / r[xs[0]]) * r[xs]):
                scalar_hits += 1  # operator agrees with c*I on the sampled coordinates
    return {"|C1|*|D|": len(U) * len(Vv), "distinct_operators_fingerprint": len(prints),
            "candidates_equal_to_scalar_on_sample": scalar_hits}


def main(cfg_path, only):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    with Experiment("quantum", "phase4_stabilizer", cfg, seed=cfg["seed"]) as ex:
        out = {}
        for spec in cfg["codes"]:
            if only and spec["key"] not in only:
                continue
            t0 = time.perf_counter()
            b = build(spec)
            code, sp = b.code, b.space
            r: dict = {"dim_H": sp.dim, "|C1|": b.C1.size, "|C2|": b.C2.size, "|D_true|": b.D_true.size,
                       "K_formula": code.K_formula, "x_generators": [b.ring.fmt(g) for g in code.xgens],
                       "z_generators": [b.ring.fmt(g) for g in code.zgens], "eps": [b.ring.fmt(e) for e in b.eps]}
            r["unitarity"] = unitarity(b, rng)
            r["pauli"] = pauli_relations(b, rng, cfg["pauli_exhaustive_limit"], cfg["pauli_pairs_sampled"])
            r["commutation_true_dual"] = code.commutation_exhaustive()
            # state-level: generators commute as operators
            psi = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
            worst = 0.0
            for u in code.xgens:
                for v in code.zgens:
                    a = sp.apply_Z(v, sp.apply_X(u, psi))
                    c = sp.apply_X(u, sp.apply_Z(v, psi))
                    worst = max(worst, float(np.abs(a - c).max()))
            r["generator_commutator_max_state_level"] = worst
            r["group_order"] = group_order(code, rng)
            pz = code.pz_diag()
            r["x_no_fixed_points"] = code.x_has_no_fixed_points()
            r["dim_trace_formula"] = code.dim_trace_formula(pz)
            r["dim_structural"] = code.dim_structural()
            V = code.logical_states(b.eps)
            G = V.conj() @ V.T
            r["logical_gram_minus_I_max"] = float(np.abs(G - np.eye(len(V))).max())
            stab = 0.0
            for v in V:
                for u in code.xgens:
                    stab = max(stab, float(np.abs(sp.apply_X(u, v) - v).max()))
                for z in code.zgens:
                    stab = max(stab, float(np.abs(sp.apply_Z(z, v) - v).max()))
            r["logical_states_stabilised_max_error"] = stab
            # P is the projector onto span(V): P^2 = P and P y = V^T V^* y for random y
            pe, ie = 0.0, 0.0
            for _ in range(cfg["projector_random_vectors"]):
                y = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
                Py = code.apply_P(y, pz)
                pe = max(pe, float(np.abs(code.apply_P(Py, pz) - Py).max()))
                ie = max(ie, float(np.abs(Py - V.T @ (V.conj() @ y)).max()))
            r["projector_idempotence_error"] = pe
            r["projector_equals_span_of_logical_states_error"] = ie
            if sp.dim <= cfg["dense_dim_limit"]:
                r["dim_dense_nullspace"] = code.dim_nullspace_dense()
            # logical operators: X(e), e in eps, and Z(w), w in C1^perp
            Ls = []
            for e in b.eps[1:3]:
                L, leak = code.logical_matrix(V, lambda s, e=e: sp.apply_X(e, s))
                Ls.append({"op": f"X({b.ring.fmt(e)})", "leakage": leak,
                           "is_permutation": bool(np.allclose(np.abs(L).round(8), np.abs(L).round(8) ** 2)
                                                  and np.allclose(np.abs(L).sum(0), 1)),
                           "trace_abs": float(abs(np.trace(L)))})
            C1d = b.C1_dual
            r["|C1_dual|"] = C1d.size
            r["logical_Z_group_size_|C1dual|/|D|"] = C1d.size / b.D_true.size
            wsel = [w for w in C1d.vectors() if not b.D_true.contains(w)][:2]
            for w in wsel:
                L, leak = code.logical_matrix(V, lambda s, w=w: sp.apply_Z(w, s))
                Ls.append({"op": f"Z({b.ring.fmt(w)})", "leakage": leak,
                           "is_diagonal": bool(np.allclose(L, np.diag(np.diag(L)))),
                           "diag_phases_distinct": len(set(np.round(np.angle(np.diag(L)), 6))) })
            r["logical_operators"] = Ls
            # Definition 6 variant
            if b.code_def6 is not None:
                c6 = b.code_def6
                r["def6"] = {"|D_def6|": b.D_def6.size, "commutation": c6.commutation_exhaustive(),
                             "dim_joint_plus1_eigenspace_structural": c6.dim_structural()}
                if sp.dim <= cfg["dense_dim_limit"]:
                    r["def6"]["dim_dense_nullspace"] = c6.dim_nullspace_dense()
            r["seconds"] = time.perf_counter() - t0
            out[spec["key"]] = r
            # PASS/FAIL against Theorem 4 (true dual)
            K = code.K_formula
            checks = {
                "X unitary": r["unitarity"]["X_is_permutation"],
                "Z unitary": r["unitarity"]["Z_unit_modulus"],
                "Pauli relation": r["pauli"]["commutation_relation_max_error"] < 1e-9,
                "stabilizers commute": r["commutation_true_dual"]["noncommuting_pairs"] == 0,
                "|S| = |C1||D|": r["group_order"]["distinct_operators_fingerprint"] == r["group_order"]["|C1|*|D|"],
                "dim = K (trace)": abs(r["dim_trace_formula"] - K) < 1e-9,
                "dim = K (structural)": r["dim_structural"] == K,
                "logical orthonormal": r["logical_gram_minus_I_max"] < 1e-12,
                "P = span(logical)": r["projector_equals_span_of_logical_states_error"] < 1e-9,
            }
            if "dim_dense_nullspace" in r:
                checks["dim = K (dense)"] = r["dim_dense_nullspace"] == K
            r["checks"] = checks
            for k, v in checks.items():
                if not v:
                    ex.fail(f"{spec['key']}: {k}")
            print(spec["key"], f"dim={sp.dim} K={K} checks={checks}")
            if "def6" in r:
                print("   def6:", r["def6"])
        ex.save_json("results.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="phase4_stabilizer.toml")
    ap.add_argument("--codes", default=None)
    a = ap.parse_args()
    main(a.config, set(a.codes.split(",")) if a.codes else None)
