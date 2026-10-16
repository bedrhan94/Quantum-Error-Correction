"""Phase 6 - noise experiments (code-capacity model) + resources + CPU/GPU scalability.

Reproducible command:
    .venv/Scripts/python.exe experiments/phase6_noise.py [--config phase6_noise.toml] [--only qubit,qudit,mc,resources]

Comparisons are made at EQUAL logical capacity K = 5:
  ring Z_25[i] code (10 qubits) | standard qudit CSS code over Z_625 (10 qubits, same Hilbert
  dimension 625) | no QEC (5 levels in 3 qubits) | [[5,1,3]] x 3 (15 qubits, standard qubit
  stabilizer code; its 8-level logical register holds the 5 levels).
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pennylane as qml
import torch

from epsqec.benchmarking import Experiment, load_config
from epsqec.css.build import build
from epsqec.noise import (five_qubit_code, five_qubit_x3_metrics, logical_channel_metrics, modular_code_embedded,
                          ring_code_embedded, unencoded_embedded)
from epsqec.noise.montecarlo import RingMC
from epsqec.pl_circuits import RingCircuits
from epsqec.pl_circuits.baselines import ModularCircuits, five_qubit_syndrome


def qubit_level(cfg, built, ex):
    ring = ring_code_embedded(built[cfg["qubit_level"]["ring_key"]])
    mod = modular_code_embedded(**cfg["qubit_level"]["modular"])
    une = unencoded_embedded(5)
    fq = five_qubit_code()
    codes = [ring, mod, une]
    rows = []
    for c in codes + [fq]:
        ce = c.completeness_error()
        if ce > 1e-12:
            ex.fail(f"{c.name}: recovery isometries incomplete ({ce})")
    use_gpu = cfg["qubit_level"]["gpu_cross_check"] and torch.cuda.is_available()
    for ch in cfg["channels"]:
        for p in cfg["p_grid"]:
            for c in codes:
                r = logical_channel_metrics(c, ch, p, device="cpu", dtype=torch.complex128)
                if use_gpu and c.n_qubits >= 10:
                    g = logical_channel_metrics(c, ch, p, device="cuda", dtype=torch.complex64)
                    r["gpu_complex64_logical_error_rate"] = g["logical_error_rate"]
                    r["gpu_seconds"] = g["seconds"]
                    r["gpu_peak_MB"] = g.get("gpu_peak_MB")
                    r["gpu_minus_cpu_abs"] = abs(g["logical_error_rate"] - r["logical_error_rate"])
                rows.append(r)
            rows.append(five_qubit_x3_metrics(fq, ch, p))
            print(ch, p, [(r["code"][:18], f"{r['logical_error_rate']:.3e}") for r in rows[-4:]])
    return rows


def qudit_level(cfg, built):
    rows = []
    for key in cfg["qudit_level"]["codes"]:
        b = built[key]
        mc = RingMC(b, "cpu")
        sp, code, R = b.space, b.code, b.ring
        V = sp.vecs
        a = np.array([mc.lutX[int(k)] for k in code.zsyn_key(V)])
        f = np.array([mc.lutZ[int(k)] for k in code.xsyn_key(V)])
        NX = int(b.C1.contains(R.sub(V, a)).sum())
        NZ = int(b.D_true.contains(R.sub(V, f)).sum())
        d = sp.dim
        K = b.C2.size // b.C1.size
        eps_bad = int((~b.C1.contains(b.eps)).sum())
        for p in cfg["qudit_level"]["p_grid"]:
            rows.append({"code": key, "hilbert_dim": d, "K": K, "p": p,
                         "LER_unit_shift_exact": 1 - mc.exact_unit_shift(p),
                         "LER_qudit_depolarizing_exact": 1 - ((1 - p) + p * (NX * NZ - 1) / (d * d - 1)),
                         "LER_unencoded_K_qudit_depolarizing": p,
                         "LER_paper_eps_error_model": p * eps_bad / len(b.eps),
                         "correctable_X_patterns": NX, "correctable_Z_patterns": NZ})
        print("qudit", key, rows[-1])
    return rows


def montecarlo(cfg, built):
    rows = []
    devices = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])
    for run in cfg["montecarlo"]["runs"]:
        b = built[run["key"]]
        for dev in devices:
            mc = RingMC(b, dev)
            t = time.perf_counter()
            r = mc.run(cfg["montecarlo"]["p"], run["trials"], run["batch"], seed=cfg["seed"])
            r.update({"code": run["key"], "hilbert_dim": b.space.dim,
                      "exact_LER": 1 - mc.exact_unit_shift(cfg["montecarlo"]["p"]),
                      "setup_plus_run_s": time.perf_counter() - t,
                      "us_per_trial": 1e6 * r["seconds"] / run["trials"]})
            k, n = r["trials"] - r["successes"], r["trials"]
            from epsqec.simulation.awgn import clopper_pearson

            r["LER_ci_low"], r["LER_ci_high"] = clopper_pearson(k, n)
            r["exact_within_CI"] = r["LER_ci_low"] <= r["exact_LER"] <= r["LER_ci_high"]
            rows.append(r)
            print("mc", run["key"], dev, {k_: r[k_] for k_ in ("logical_error_rate", "exact_LER", "exact_within_CI",
                                                               "seconds", "us_per_trial")}, r.get("gpu_peak_MB"))
    return rows


def _specs(body, n_wires, gate_set):
    dev = qml.device("default.qubit", wires=n_wires)

    @qml.qnode(dev)
    def c():
        body()
        return qml.probs(wires=0)

    dec = qml.transforms.decompose(c, gate_set=set(gate_set))
    s = qml.specs(dec, level="user", compute_depth=True)()
    res = s.resources if hasattr(s, "resources") else s
    two_q = sum(int(v) for k, v in res.gate_types.items() if k in ("CNOT", "CZ", "CY", "ControlledPhaseShift", "SWAP"))
    return {"wires": n_wires, "num_gates": int(res.num_gates), "depth": res.depth,
            "two_qubit_gates": two_q, "three_qubit_gates": int(res.gate_types.get("Toffoli", 0)),
            "gate_types": {str(k): int(v) for k, v in res.gate_types.items()}}


def resources(cfg, built):
    gs = cfg["resources"]["gate_set"]
    out = {}
    b = built["Z25"]
    rc = RingCircuits(25, zgens=b.code.zgens, xgens=b.code.xgens)
    out["ring Z_25[i]"] = _specs(lambda: ([rc.z_syndrome(k) for k in range(len(rc.zgens))],
                                          [rc.x_syndrome(k) for k in range(len(rc.xgens))],
                                          rc.X((1, 0)), rc.Z((1, 0))), rc.L.n_wires, gs)
    mcirc = ModularCircuits(**cfg["qubit_level"]["modular"])
    out["modular Z_625"] = _specs(lambda: (mcirc.z_syndrome(), mcirc.x_syndrome(), mcirc.X(1), mcirc.Z(1)),
                                  mcirc.n_wires, gs)
    one = _specs(lambda: five_qubit_syndrome(), 9, gs)
    out["[[5,1,3]] x 3"] = {k: (v * 3 if isinstance(v, int) else v) for k, v in one.items() if k != "gate_types"}
    out["[[5,1,3]] x 3"]["wires"] = 27
    out["[[5,1,3]] x 3"]["note"] = "3 independent blocks, 9 wires each (5 data + 4 ancilla); depth of one block"
    out["[[5,1,3]] x 3"]["depth"] = one["depth"]
    out["no QEC"] = {"wires": 3, "num_gates": 0, "depth": 0, "two_qubit_gates": 0}
    for k, v in out.items():
        print("resources", k, {kk: v.get(kk) for kk in ("wires", "num_gates", "depth", "two_qubit_gates", "three_qubit_gates")})
    return out


def main(cfg_path, only):
    cfg = load_config(cfg_path)
    want = lambda s: only is None or s in only
    with Experiment("quantum", "phase6_noise", cfg, seed=cfg["seed"]) as ex:
        built = {spec["key"]: build(spec) for spec in cfg["codes"]}
        out = {"noise_model": "code capacity: i.i.d. single-qubit (or qudit) noise on the data once; ideal "
                              "encoding/syndrome extraction/recovery"}
        if want("resources"):
            out["resources"] = resources(cfg, built)
        if want("qudit"):
            q = qudit_level(cfg, built)
            ex.save_csv("qudit_level.csv", q)
        if want("mc"):
            m = montecarlo(cfg, built)
            ex.save_csv("montecarlo_cpu_gpu.csv", m)
            for r in m:
                if not r["exact_within_CI"]:
                    ex.note(f"MC {r['code']} {r['device']}: exact value outside 95% CI")
        if want("qubit"):
            rows = qubit_level(cfg, built, ex)
            ex.save_csv("qubit_level.csv", rows)
        ex.save_json("results.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="phase6_noise.toml")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    main(a.config, set(a.only.split(",")) if a.only else None)
