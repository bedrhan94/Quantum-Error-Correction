"""Phase 5 (circuits) - PennyLane prototypes: gates, leakage, Prop. 5 in a circuit, QEC cycle.

Reproducible command:
    .venv/Scripts/python.exe experiments/phase5_pennylane.py [--config phase5_pennylane.toml] [--only gates,prop5,xsyn,cycle,specs]
"""
from __future__ import annotations

import argparse
import time
import tracemalloc

import numpy as np
import pennylane as qml

from epsqec.benchmarking import Experiment, load_config
from epsqec.css.build import build
from epsqec.pl_circuits import RingCircuits
from epsqec.pl_circuits.ring_circuits import nbits
from epsqec.stabilizer import min_weight_transversal


# ----------------------------------------------------------------------------- helpers
DEVICE_KW: dict = {}  # e.g. {"c_dtype": np.complex64} for lightning.gpu; set from the config in main()


def gpu_mem_used_MB():
    """Device-wide used memory from nvidia-smi (lightning.gpu allocates outside torch)."""
    import subprocess

    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20)
        return float(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


def run_state(dev_name, n_wires, body):
    dev = qml.device(dev_name, wires=n_wires, **DEVICE_KW)

    @qml.qnode(dev)
    def circ():
        body()
        return qml.state()

    t = time.perf_counter()
    st = np.asarray(circ())
    dt = time.perf_counter() - t
    if dev_name == "lightning.gpu":
        run_state.last_gpu_MB = gpu_mem_used_MB()
    return st, dt, circ


def split_state(st, rc: RingCircuits):
    """full state -> (data states per ancilla value, probabilities of ancilla values)."""
    nd = 2 * rc.L.m
    rest = rc.L.n_wires - nd
    M = st.reshape(2 ** nd, 2 ** rest)
    p = (np.abs(M) ** 2).sum(axis=0)
    return M, p


def anc_value(rest_index: int, rc: RingCircuits, reg: list[int]) -> int:
    """Value of an ancilla register given the index over all non-data wires."""
    nd = 2 * rc.L.m
    rest = rc.L.n_wires - nd
    bits = [(rest_index >> (rest - 1 - (w - nd))) & 1 for w in reg]
    return int("".join(map(str, bits)), 2) if bits else 0


def random_ring_state(rng, dim):
    v = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    return v / np.linalg.norm(v)


def random_logical(V, rng):
    c = rng.normal(size=len(V)) + 1j * rng.normal(size=len(V))
    c /= np.linalg.norm(c)
    return c @ V


# ----------------------------------------------------------------------------- tests
def adder_leakage(q, ks) -> dict:
    """qml.matrix of Adder(k) on (m register wires + 2 work wires): exact action on every basis input."""
    m = nbits(q)
    wires = list(range(m))
    work = [m, m + 1]
    res = {"q": q, "m": m, "k_tested": len(ks), "valid_inputs_correct": True, "work_wires_clean_valid": True,
           "invalid_inputs": 2 ** m - q, "invalid_stay_invalid": True, "work_wires_clean_invalid": True,
           "is_permutation": True}
    dense = m <= 7  # qml.matrix on m+2 <= 9 wires; otherwise simulate every basis input
    res["method"] = "qml.matrix (dense, verification only)" if dense else "basis-state simulation, lightning.qubit"
    if not dense:
        res.pop("is_permutation")
        dev = qml.device("lightning.qubit", wires=m + 2)
    for k in ks:
        if dense:
            U = qml.matrix(qml.Adder(int(k), wires, mod=q, work_wires=work), wire_order=wires + work)
            A = np.abs(U)
            if not (np.allclose(A.sum(0), 1) and np.allclose(A.sum(1), 1) and np.allclose(A * A, A, atol=1e-8)):
                res["is_permutation"] = False
        for x in range(2 ** m):
            if dense:
                col = U[:, x << 2]  # work wires |00>
            else:
                @qml.qnode(dev)
                def c():
                    qml.BasisEmbedding(x, wires=wires)
                    qml.Adder(int(k), wires, mod=q, work_wires=work)
                    return qml.state()
                col = np.asarray(c())
            out = int(np.argmax(np.abs(col)))
            y, wk = out >> 2, out & 3
            if x < q:
                if y != (x + k) % q:
                    res["valid_inputs_correct"] = False
                if wk != 0:
                    res["work_wires_clean_valid"] = False
            else:
                if y < q:
                    res["invalid_stay_invalid"] = False
                if wk != 0:
                    res["work_wires_clean_invalid"] = False
    return res


def gate_tests(b, rng, dev, n_u):
    R, sp = b.ring, b.space
    rc = RingCircuits(R.q)
    nw = rc.L.n_wires
    us = [np.asarray(g).reshape(2) for g in b.code.xgens + b.code.zgens] + [sp.vecs[i, 0] for i in rng.integers(0, sp.dim, n_u)]
    worstX = worstZ = 0.0
    leak = 0.0
    tX = tZ = 0.0
    for u in us:
        psi = random_ring_state(rng, sp.dim)
        init = np.zeros(2 ** nw, dtype=complex)
        init.reshape(2 ** (2 * rc.L.m), 4)[:, 0] = rc.embed_ring_state(psi)
        st, dt, _ = run_state(dev, nw, lambda: (qml.StatePrep(init, wires=range(nw)), rc.X(u)))
        tX += dt
        M, p = split_state(st, rc)
        out, lk = rc.extract_ring_state(M[:, 0])
        leak = max(leak, lk, 1 - p[0])
        worstX = max(worstX, float(np.abs(out - sp.apply_X(u[None], psi)).max()))
        st, dt, _ = run_state(dev, nw, lambda: (qml.StatePrep(init, wires=range(nw)), rc.Z(u)))
        tZ += dt
        M, _ = split_state(st, rc)
        out, _ = rc.extract_ring_state(M[:, 0])
        worstZ = max(worstZ, float(np.abs(out - sp.apply_Z(u[None], psi)).max()))
    return {"n_ops": len(us), "wires": nw, "X_max_abs_error_vs_reference": worstX,
            "Z_max_abs_error_vs_reference": worstZ, "max_leakage_or_dirty_work": leak,
            "seconds_X": tX, "seconds_Z": tZ}


def prop5_circuit(b, rng, dev, max_wires):
    """X(e), e in eps, on a random logical state; Z-type syndrome extracted into ancillas."""
    R, sp, code = b.ring, b.space, b.code
    rc = RingCircuits(R.q, zgens=code.zgens)
    nw = rc.L.n_wires
    if nw > max_wires:
        return {"status": "NOT RUN", "reason": f"{nw} wires > max_wires={max_wires}"}
    V = code.logical_states(b.eps)
    psi = random_logical(V, rng)
    init_data = rc.embed_ring_state(psi)
    rows = []
    for e in b.eps:
        e2 = e.reshape(2)
        init = np.zeros(2 ** nw, dtype=complex)
        init.reshape(2 ** (2 * rc.L.m), -1)[:, 0] = init_data

        def body():
            qml.StatePrep(init, wires=range(nw))
            rc.X(e2)
            for k in range(len(rc.zgens)):
                rc.z_syndrome(k)

        tracemalloc.start()
        st, dt, circ = run_state(dev, nw, body)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        M, p = split_state(st, rc)
        j = int(np.argmax(p))
        synd = tuple(rc.z_syndrome_value(k, anc_value(j, rc, rc.L.z_anc[k])) for k in range(len(rc.zgens)))
        data, lk = rc.extract_ring_state(M[:, j] / np.sqrt(p[j]))
        fid_orig = float(abs(np.vdot(psi, data)) ** 2)
        fid_shift = float(abs(np.vdot(sp.apply_X(e, psi), data)) ** 2)
        rows.append({"e": R.fmt(e2), "syndrome_measured": synd, "syndrome_probability": float(p[j]),
                     "syndrome_algebraic": tuple(int(x) for x in code.zsyn(e[None])[0]),
                     "fidelity_with_original_logical_state": fid_orig,
                     "fidelity_with_X(e)psi": fid_shift, "leakage": lk, "seconds": dt,
                     "python_peak_MB": peak / 2**20})
    return {"status": "RUN", "wires": nw, "rows": rows,
            "distinct_measured_syndromes": len({r["syndrome_measured"] for r in rows}), "|eps|": len(rows)}


def x_syndrome_circuit(b, rng, dev, max_wires, n_errors=8):
    """Z(f) errors with f in T_Z: X-type syndrome by phase estimation vs algebraic xsyn.
    If all generators together need more than max_wires, each generator is measured in its own
    circuit (valid: Pauli-error states are joint eigenstates, so every syndrome bit is deterministic)."""
    R, sp, code = b.ring, b.space, b.code
    rc_all = RingCircuits(R.q, xgens=code.xgens)
    groups = [list(range(len(code.xgens)))]
    mode = "all generators in one circuit"
    if rc_all.L.n_wires > max_wires:
        groups = [[k] for k in range(len(code.xgens))]
        mode = "one circuit per generator"
    rcs = [RingCircuits(R.q, xgens=[code.xgens[k] for k in g]) for g in groups]
    widths = [rc.L.n_wires for rc in rcs]
    if max(widths) > max_wires:
        return {"status": "NOT RUN", "reason": f"{max(widths)} wires > max_wires={max_wires}", "mode": mode}
    C1d = b.C1_dual
    TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // C1d.size)
    V = code.logical_states(b.eps)
    psi = random_logical(V, rng)
    sel = TZ[: min(len(TZ), n_errors)]
    rows = []
    for f in sel:
        synd = [None] * len(code.xgens)
        prob, secs, gpu = 1.0, 0.0, []
        for g, rc in zip(groups, rcs):
            nw = rc.L.n_wires
            init = np.zeros(2 ** nw, dtype=complex)
            init.reshape(2 ** (2 * rc.L.m), -1)[:, 0] = rc.embed_ring_state(psi)

            def body():
                qml.StatePrep(init, wires=range(nw))
                rc.Z(f.reshape(2))
                for k in range(len(rc.xgens)):
                    rc.x_syndrome(k)

            st, dt, _ = run_state(dev, nw, body)
            secs += dt
            gpu.append(getattr(run_state, "last_gpu_MB", None))
            M, p = split_state(st, rc)
            j = int(np.argmax(p))
            prob *= float(p[j])
            for kk, k in enumerate(g):
                synd[k] = rc.x_syndrome_value(kk, anc_value(j, rc, rc.L.x_anc[kk]))
            del st, M
        rows.append({"f": R.fmt(f.reshape(2)), "syndrome_measured": tuple(synd), "probability": prob,
                     "syndrome_algebraic": tuple(int(x) for x in code.xsyn(f[None])[0]), "seconds": secs,
                     "gpu_used_MB_after_run": gpu})
        print("   xsyn", R.fmt(f.reshape(2)), tuple(synd), round(secs, 1), flush=True)
    ok = all(r["syndrome_measured"] == r["syndrome_algebraic"] and r["probability"] > 1 - 1e-9 for r in rows)
    return {"status": "RUN", "wires": max(widths), "circuit_widths": widths, "mode": mode,
            "x_anc_orders": rc_all.x_orders, "rows": rows, "all_match": ok}


def full_cycle_coherent(b, rng, dev, n_pairs, max_wires):
    """ALTERNATIVE DESIGN, coherent feed-forward: corrections are applied as gates controlled on the
    syndrome ancilla registers (deferred-measurement principle, physically equivalent to measuring
    the ancillas and correcting classically).  Allows returning qml.state() on large registers."""
    R, sp, code = b.ring, b.space, b.code
    rc = RingCircuits(R.q, zgens=code.zgens, xgens=code.xgens)
    nw = rc.L.n_wires
    if nw > max_wires:
        return {"status": "NOT RUN", "reason": f"{nw} wires > max_wires={max_wires}"}
    assert len(rc.zgens) == 1 and len(rc.xgens) == 1, "written for single generators"
    TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // b.C2.size)
    TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // b.C1_dual.size)
    lutX = {tuple(int(x) for x in code.zsyn(a[None])[0]): a.reshape(2) for a in TX}
    lutZ = {tuple(int(x) for x in code.xsyn(f[None])[0]): f.reshape(2) for f in TZ}
    V = code.logical_states(b.eps)
    psi = random_logical(V, rng)
    data0 = rc.embed_ring_state(psi)
    pairs = [(TX[i], TZ[j]) for i, j in zip(rng.integers(0, len(TX), n_pairs), rng.integers(0, len(TZ), n_pairs))]
    bits = lambda v, n: [(v >> (n - 1 - i)) & 1 for i in range(n)]
    rows = []
    for a, f in pairs:
        init = np.zeros(2 ** nw, dtype=complex)
        init.reshape(2 ** (2 * rc.L.m), -1)[:, 0] = data0
        zw, xw = rc.L.z_anc[0], rc.L.x_anc[0]

        def body():
            qml.StatePrep(init, wires=range(nw))
            rc.X(a.reshape(2))
            rc.Z(f.reshape(2))
            rc.z_syndrome(0)
            rc.x_syndrome(0)
            for sprime in range(rc.z_orders[0]):
                corr = lutX.get((rc.z_syndrome_value(0, sprime),))
                if corr is not None and np.any(corr):
                    rc.X(R.neg(corr), control=zw, control_values=bits(sprime, len(zw)))
            for lam in range(rc.x_orders[0]):
                corr = lutZ.get((rc.x_syndrome_value(0, lam),))
                if corr is not None and np.any(corr):
                    rc.Z(R.neg(corr), control=xw, control_values=bits(lam, len(xw)))

        st, dt, _ = run_state(dev, nw, body)
        M, p = split_state(st, rc)
        j = int(np.argmax(p))
        data = M[:, j] / np.sqrt(p[j])
        fid = float(abs(np.vdot(data0, data)) ** 2)
        rows.append({"a": R.fmt(a.reshape(2)), "b": R.fmt(f.reshape(2)), "ancilla_branch_probability": float(p[j]),
                     "fidelity_after_recovery": fid, "seconds": dt,
                     "gpu_used_MB_after_run": getattr(run_state, "last_gpu_MB", None)})
        print("   cycle", rows[-1]["a"], rows[-1]["b"], round(fid, 12), round(dt, 1), flush=True)
        del st, M
    return {"status": "RUN", "label": "ALTERNATIVE DESIGN - not a result of the paper", "wires": nw,
            "feed_forward": "coherent (ancilla-controlled corrections)", "rows": rows,
            "min_fidelity": min(r["fidelity_after_recovery"] for r in rows)}


def full_cycle(b, rng, dev, n_pairs, max_wires):
    """ALTERNATIVE DESIGN: error X(a)Z(b) -> both syndromes measured mid-circuit -> feed-forward
    recovery with qml.cond -> final data state compared to the encoded state."""
    R, sp, code = b.ring, b.space, b.code
    rc = RingCircuits(R.q, zgens=code.zgens, xgens=code.xgens)
    nw = rc.L.n_wires
    if nw > max_wires:
        return {"status": "NOT RUN", "reason": f"{nw} wires > max_wires={max_wires}"}
    C1d = b.C1_dual
    TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // b.C2.size)
    TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // C1d.size)
    lutX = {tuple(int(x) for x in code.zsyn(a[None])[0]): a.reshape(2) for a in TX}
    lutZ = {tuple(int(x) for x in code.xsyn(f[None])[0]): f.reshape(2) for f in TZ}
    V = code.logical_states(b.eps)
    psi = random_logical(V, rng)
    data0 = rc.embed_ring_state(psi)
    pairs = [(TX[i], TZ[j]) for i, j in zip(rng.integers(0, len(TX), n_pairs), rng.integers(0, len(TZ), n_pairs))]
    # one register each (single generators for Z25); recovery branches over measured values
    assert len(rc.zgens) == 1 and len(rc.xgens) == 1, "feed-forward cycle written for single generators"
    rows = []
    for a, f in pairs:
        dev_ = qml.device(dev, wires=nw)

        @qml.qnode(dev_, mcm_method="deferred")
        def circ():
            init = np.zeros(2 ** nw, dtype=complex)
            init.reshape(2 ** (2 * rc.L.m), -1)[:, 0] = data0
            qml.StatePrep(init, wires=range(nw))
            rc.X(a.reshape(2))
            rc.Z(f.reshape(2))
            rc.z_syndrome(0)
            rc.x_syndrome(0)
            mz = [qml.measure(w) for w in rc.L.z_anc[0]]
            mx = [qml.measure(w) for w in rc.L.x_anc[0]]
            vz = sum(m * (1 << (len(mz) - 1 - i)) for i, m in enumerate(mz))
            vx = sum(m * (1 << (len(mx) - 1 - i)) for i, m in enumerate(mx))
            for sprime in range(rc.z_orders[0]):
                corr = lutX.get((rc.z_syndrome_value(0, sprime),))
                if corr is not None and np.any(corr):
                    qml.cond(vz == sprime, rc.X)(R.neg(corr))
            for lam in range(rc.x_orders[0]):
                corr = lutZ.get((rc.x_syndrome_value(0, lam),))
                if corr is not None and np.any(corr):
                    qml.cond(vx == lam, rc.Z)(R.neg(corr))
            return qml.density_matrix(wires=rc.L.data)

        t = time.perf_counter()
        rho = np.asarray(circ())
        dt = time.perf_counter() - t
        fid = float(np.real(np.vdot(data0, rho @ data0)))
        rows.append({"a": R.fmt(a.reshape(2)), "b": R.fmt(f.reshape(2)), "fidelity_after_recovery": fid, "seconds": dt})
    return {"status": "RUN", "label": "ALTERNATIVE DESIGN - not a result of the paper", "wires": nw,
            "mcm_method": "deferred", "rows": rows, "min_fidelity": min(r["fidelity_after_recovery"] for r in rows)}


def circuit_specs(b, dev, gate_set):
    """Gate counts / depth of one Z-syndrome round and one X(u) gate, decomposed to `gate_set`."""
    code = b.code
    rc = RingCircuits(b.ring.q, zgens=code.zgens, xgens=code.xgens)
    out = {}
    progs = {
        "X(u) one generator": lambda: rc.X(np.asarray(code.xgens[0]).reshape(2)),
        "Z(v) one generator": lambda: rc.Z(np.asarray(code.zgens[0]).reshape(2)),
        "Z-type syndrome round": lambda: [rc.z_syndrome(k) for k in range(len(rc.zgens))],
        "X-type syndrome round": lambda: [rc.x_syndrome(k) for k in range(len(rc.xgens))],
    }
    for name, body in progs.items():
        devx = qml.device("default.qubit", wires=rc.L.n_wires)

        @qml.qnode(devx)
        def c():
            body()
            return qml.probs(wires=0)

        try:
            dec = qml.transforms.decompose(c, gate_set=set(gate_set))
            s = qml.specs(dec, level="user", compute_depth=True)()
            res = s.resources if hasattr(s, "resources") else s
            out[name] = {"wires_allocated": rc.L.n_wires, "num_gates": int(res.num_gates),
                         "depth": int(res.depth) if res.depth is not None else None,
                         "gate_types": {str(k): int(v) for k, v in res.gate_types.items()}}
        except Exception as exc:  # recorded, not hidden
            out[name] = {"error": repr(exc)[:300]}
    return out


def main(cfg_path, only):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    dev = cfg["device"]
    want = lambda s: only is None or s in only
    if cfg.get("c_dtype"):
        DEVICE_KW["c_dtype"] = {"complex64": np.complex64, "complex128": np.complex128}[cfg["c_dtype"]]
    with Experiment("quantum", cfg.get("experiment_name", "phase5_pennylane"), cfg, seed=cfg["seed"]) as ex:
        out = {"pennylane_version": qml.__version__, "device": dev, "c_dtype": cfg.get("c_dtype", "complex128")}
        built = {spec["key"]: build(spec) for spec in cfg["codes"]}
        if want("gates"):
            out["adder_leakage"] = {}
            for key in cfg["gate_tests"]:
                q = built[key].ring.q
                ks = list(range(q)) if q <= cfg["adder_all_k_limit"] else list(rng.integers(1, q, cfg["adder_sample_k"]))
                t = time.perf_counter()
                out["adder_leakage"][key] = adder_leakage(q, ks)
                out["adder_leakage"][key]["seconds"] = time.perf_counter() - t
                print("adder", key, out["adder_leakage"][key])
            out["gate_tests"] = {}
            for key in cfg["gate_tests"]:
                out["gate_tests"][key] = gate_tests(built[key], rng, dev, cfg["gate_test_random_u"])
                print("gates", key, out["gate_tests"][key])
                g = out["gate_tests"][key]
                if g["X_max_abs_error_vs_reference"] > 1e-8 or g["Z_max_abs_error_vs_reference"] > 1e-8:
                    ex.fail(f"{key}: gate decomposition disagrees with reference")
        if want("prop5"):
            out["prop5_circuit"] = {}
            for key in cfg["prop5_z_syndrome"]:
                r = prop5_circuit(built[key], rng, dev, cfg["max_wires"])
                out["prop5_circuit"][key] = r
                print("prop5", key, r.get("status"), [(x["e"], x["syndrome_measured"], round(x["fidelity_with_original_logical_state"], 4),
                                                       round(x["fidelity_with_X(e)psi"], 6), round(x["seconds"], 1)) for x in r.get("rows", [])])
        if want("xsyn"):
            out["x_syndrome_circuit"] = {}
            for key in cfg["x_syndrome"]:
                r = x_syndrome_circuit(built[key], rng, dev, cfg["max_wires"],
                                       cfg.get("x_syndrome_errors", {}).get(key, 8))
                out["x_syndrome_circuit"][key] = r
                print("xsyn", key, r.get("status"), r.get("all_match"), [(x["f"], x["syndrome_measured"], x["syndrome_algebraic"]) for x in r.get("rows", [])])
                if r.get("status") == "RUN" and not r["all_match"]:
                    ex.fail(f"{key}: X-type syndrome circuit disagrees with algebra")
                ex.save_json("results_partial.json", out)
        if want("cycle"):
            out["full_cycle"] = {}
            for key in cfg["full_cycle"]:
                r = full_cycle(built[key], rng, dev, cfg["full_cycle_pairs"], cfg["max_wires"])
                out["full_cycle"][key] = r
                print("cycle", key, r.get("status"), r.get("min_fidelity"), [(x["a"], x["b"], round(x["fidelity_after_recovery"], 9)) for x in r.get("rows", [])])
                if r.get("status") == "RUN" and r["min_fidelity"] < 1 - 1e-8:
                    ex.fail(f"{key}: full QEC cycle did not restore the state")
        if want("cycle_coherent"):
            out["full_cycle_coherent"] = {}
            for key in cfg.get("full_cycle_coherent", []):
                r = full_cycle_coherent(built[key], rng, dev, cfg.get("full_cycle_coherent_pairs", 4), cfg["max_wires"])
                out["full_cycle_coherent"][key] = r
                print("cycle_coherent", key, r.get("status"), r.get("min_fidelity"))
                if r.get("status") == "RUN" and r["min_fidelity"] < 1 - 1e-6:
                    ex.fail(f"{key}: coherent QEC cycle did not restore the state")
            ex.save_json("results_partial.json", out)
        if want("specs"):
            out["specs"] = {}
            for key in ("Z25", "Z85", "Z325"):
                out["specs"][key] = circuit_specs(built[key], dev, cfg["gate_set"])
                print("specs", key, {k: (v.get("num_gates"), v.get("depth"), v.get("error")) for k, v in out["specs"][key].items()})
        ex.save_json("results.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="phase5_pennylane.toml")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    main(a.config, set(a.only.split(",")) if a.only else None)
