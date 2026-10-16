"""lightning.qubit (CPU) vs lightning.gpu (cuStateVec, complex128 / complex64) on the same circuits.

Run inside WSL2 (lightning.gpu is Linux-only):
    ~/venvs/epsqec/bin/python experiments/bench_pennylane_devices.py
For every circuit the output state of each device is compared with the lightning.qubit
complex128 state (fidelity), and wall time / GPU memory are recorded.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pennylane as qml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase5_pennylane as P  # noqa: E402

from epsqec.benchmarking import Experiment  # noqa: E402
from epsqec.css.build import build  # noqa: E402
from epsqec.pl_circuits import RingCircuits  # noqa: E402
from epsqec.stabilizer import min_weight_transversal  # noqa: E402

DEVICES = [("lightning.qubit", np.complex128), ("lightning.gpu", np.complex128), ("lightning.gpu", np.complex64)]


def prop5_body(b, rc, psi, e):
    nw = rc.L.n_wires
    init = np.zeros(2 ** nw, dtype=complex)
    init.reshape(2 ** (2 * rc.L.m), -1)[:, 0] = rc.embed_ring_state(psi)

    def body():
        qml.StatePrep(init, wires=range(nw))
        rc.X(e.reshape(2))
        rc.z_syndrome(0)

    return body


def xsyn_body(b, rc, psi, f):
    nw = rc.L.n_wires
    init = np.zeros(2 ** nw, dtype=complex)
    init.reshape(2 ** (2 * rc.L.m), -1)[:, 0] = rc.embed_ring_state(psi)

    def body():
        qml.StatePrep(init, wires=range(nw))
        rc.Z(f.reshape(2))
        rc.x_syndrome(0)

    return body


def main():
    cfg = {"devices": [f"{d}:{np.dtype(t).name}" for d, t in DEVICES], "seed": 9, "repeats": 2}
    rng = np.random.default_rng(cfg["seed"])
    with Experiment("benchmarks", "bench_pennylane_devices", cfg, seed=cfg["seed"]) as ex:
        jobs = []
        for key in ("Z25", "Z85", "Z325"):
            b = build({"key": key})
            V = b.code.logical_states(b.eps)
            c = rng.normal(size=len(V)) + 1j * rng.normal(size=len(V))
            psi = (c / np.linalg.norm(c)) @ V
            rc = RingCircuits(b.ring.q, zgens=b.code.zgens)
            jobs.append((f"{key} Prop.5 Z-syndrome round", rc, prop5_body(b, rc, psi, b.eps[1])))
            if key == "Z85":
                rcx = RingCircuits(b.ring.q, xgens=b.code.xgens)
                TZ = min_weight_transversal(b.space, b.code.xsyn_key, b.space.dim // b.C1_dual.size)
                jobs.append((f"{key} X-syndrome round (phase estimation)", rcx, xsyn_body(b, rcx, psi, TZ[1])))
        rows = []
        for name, rc, body in jobs:
            ref = None
            for dev, dt in DEVICES:
                P.DEVICE_KW.clear()
                P.DEVICE_KW["c_dtype"] = dt
                times = []
                for _ in range(cfg["repeats"]):
                    st, sec, _ = P.run_state(dev, rc.L.n_wires, body)
                    times.append(sec)
                st = st.astype(np.complex128)
                if ref is None:
                    ref = st
                fid = float(abs(np.vdot(ref, st)) ** 2)
                row = {"circuit": name, "wires": rc.L.n_wires, "device": dev, "c_dtype": np.dtype(dt).name,
                       "seconds_min": min(times), "seconds_all": times, "fidelity_vs_lightning_qubit_c128": fid,
                       "gpu_used_MB_after_run": getattr(P.run_state, "last_gpu_MB", None) if dev == "lightning.gpu" else None}
                rows.append(row)
                print(row, flush=True)
                del st
        for r in rows:
            base = next(x for x in rows if x["circuit"] == r["circuit"] and x["device"] == "lightning.qubit")
            r["speedup_vs_lightning_qubit"] = base["seconds_min"] / r["seconds_min"]
            # single precision accumulates ~1e-7 relative error per gate over ~1e4 gates -> allow 1e-4
            tol = 1e-4 if r["c_dtype"] == "complex64" else 1e-9
            r["fidelity_tolerance"] = tol
            if r["fidelity_vs_lightning_qubit_c128"] < 1 - tol:
                ex.fail(f"{r['circuit']} {r['device']} {r['c_dtype']}: fidelity {r['fidelity_vs_lightning_qubit_c128']}")
        ex.save_csv("bench_pennylane_devices.csv", rows)
        ex.save_json("results.json", {"rows": rows})


if __name__ == "__main__":
    main()
