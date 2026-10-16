"""Step 6 - noise after the gate-level steps 1-5 passed: qudit level (exact + Monte Carlo) and qubit
level for layouts A and B with equal K and explicit qubit counts.

    .venv/Scripts/python.exe experiments/noise_layouts.py [--config noise_layouts.toml]

Noise model: code capacity (each physical qubit / qudit coordinate hit once, ideal syndrome
extraction and recovery).  Uncoded references:
  qudit level : K-level qudit with one X and one Z coordinate (unit shifts):  LER = 1 - (1-p)^2;
                the ring qudit itself without encoding (2 + 2 coordinates):   LER = 1 - (1-p)^4;
                K-level qudit depolarizing:                                    LER = p
  qubit level : minimal 3 qubits; SAME register and qubit count as the code (layout A 10 q,
                layout B 12 q) with strict decoding; layout B label-digit-only decoding (12 q).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from epsqec.benchmarking import Experiment, load_config
from epsqec.css.build import build
from epsqec.noise import (five_qubit_code, five_qubit_x3_metrics, logical_channel_metrics, ring_code_embedded,
                          unencoded_embedded)
from epsqec.noise.codes import ring_code_embedded_split, uncoded_label_only, uncoded_same_embedding
from epsqec.noise.montecarlo import RingMC
from epsqec.simulation.awgn import clopper_pearson

ROOT = Path(__file__).resolve().parents[1]


def gate_level_status(prefix) -> tuple[str, dict]:
    runs = sorted((ROOT / "results" / "quantum").glob(f"{prefix}-*"))
    for d in reversed(runs):
        f = d / "results.json"
        if f.exists():
            r = json.loads(f.read_text(encoding="utf-8"))
            return d.name, {k: all(s.get("status") == "PASS" for s in v["steps"].values()) for k, v in r["codes"].items()}
    return "none", {}


def qudit_level(b, cfg, key, rng) -> list[dict]:
    mc = RingMC(b, "cpu")
    sp, code, R = b.space, b.code, b.ring
    V = sp.vecs
    a = np.array([mc.lutX[int(k)] for k in code.zsyn_key(V)])
    f = np.array([mc.lutZ[int(k)] for k in code.xsyn_key(V)])
    NX = int(b.C1.contains(R.sub(V, a)).sum())
    NZ = int(b.D_true.contains(R.sub(V, f)).sum())
    d, K = sp.dim, b.C2.size // b.C1.size
    rows = []
    for p in cfg["p_grid"]:
        rows.append({"code": key, "hilbert_dim": d, "K": K, "p": p,
                     "LER_unit_shift_exact": 1 - mc.exact_unit_shift(p),
                     "LER_uncoded_K_qudit_unit_shift": 1 - (1 - p) ** 2,
                     "LER_uncoded_ring_qudit_unit_shift": 1 - (1 - p) ** 4,
                     "LER_qudit_depolarizing_exact": 1 - ((1 - p) + p * (NX * NZ - 1) / (d * d - 1)),
                     "LER_uncoded_K_qudit_depolarizing": p})
    return rows


def qudit_mc(b, cfg, key) -> list[dict]:
    out = []
    for dev in ["cpu"] + (["cuda"] if torch.cuda.is_available() else []):
        mc = RingMC(b, dev)
        r = mc.run(cfg["mc_p"], cfg["mc_trials"][key], cfg["mc_batch"][key], seed=11)
        lo, hi = clopper_pearson(r["trials"] - r["successes"], r["trials"])
        ex = 1 - mc.exact_unit_shift(cfg["mc_p"])
        out.append({**r, "code": key, "exact_LER": ex, "ci_low": lo, "ci_high": hi, "exact_within_CI": lo <= ex <= hi})
    return out


def qubit_level(b, cfg, log) -> list[dict]:
    codes = {
        "ring layout A (10 q)": (ring_code_embedded(b), "cpu"),
        "ring layout B (12 q)": (ring_code_embedded_split(b), "cuda" if torch.cuda.is_available() else "cpu"),
        "no QEC minimal (3 q)": (unencoded_embedded(5), "cpu"),
        "no QEC same register A (10 q, strict)": (uncoded_same_embedding(b, "A"), "cpu"),
        "no QEC same register B (12 q, strict)": (uncoded_same_embedding(b, "B"), "cuda" if torch.cuda.is_available() else "cpu"),
        "no QEC layout B, label digit only (12 q)": (uncoded_label_only(b), "cuda" if torch.cuda.is_available() else "cpu"),
    }
    fq = five_qubit_code()
    rows = []
    for ch in cfg["channels"]:
        for p in cfg["p_grid"]:
            for name, (c, dev) in codes.items():
                dt = torch.complex64 if dev == "cuda" else torch.complex128
                r = logical_channel_metrics(c, ch, p, device=dev, dtype=dt, chunk=cfg["gpu_chunk"])
                r.update({"code": name, "physical_qubits": c.n_qubits, "dtype": str(dt).replace("torch.", "")})
                rows.append(r)
            r = five_qubit_x3_metrics(fq, ch, p)
            r["code"] = "[[5,1,3]] x 3 (15 q)"
            rows.append(r)
            log(f"{ch} p={p}: " + ", ".join(f"{x['code'][:22]}={x['logical_error_rate']:.3e}" for x in rows[-7:]))
    # CPU complex128 cross-check of the GPU (complex64) layout-B rows
    cB = codes["ring layout B (12 q)"][0]
    for ch in cfg["channels"]:
        r = logical_channel_metrics(cB, ch, cfg["cpu_crosscheck_p"], device="cpu", dtype=torch.complex128, chunk=cfg["gpu_chunk"])
        g = [x for x in rows if x["code"] == "ring layout B (12 q)" and x["channel"] == ch and x["p"] == cfg["cpu_crosscheck_p"]][0]
        g["cpu_complex128_LER"] = r["logical_error_rate"]
        g["gpu_minus_cpu_abs"] = abs(g["logical_error_rate"] - r["logical_error_rate"])
    return rows


def main(cfg_path):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    with Experiment("quantum", "noise_layouts", cfg, seed=cfg["seed"]) as ex:
        src, status = gate_level_status(cfg["gate_level_prefix"])
        out = {"gate_level_source": src, "gate_level_all_steps_pass": status, "qudit": {}, "qubit": None}
        print("gate-level source", src, status)
        built = {s["key"]: build(s) for s in cfg["codes"]}
        qrows, mrows = [], []
        for key in cfg["qudit"]["codes"]:
            if not status.get(key):
                out["qudit"][key] = "NOT RUN (gate-level steps 1-5 not all PASS)"
                ex.note(f"{key}: noise NOT RUN (gate-level gate not passed)")
                continue
            qrows += qudit_level(built[key], cfg["qudit"], key, rng)
            mrows += qudit_mc(built[key], cfg["qudit"], key)
            out["qudit"][key] = "RUN"
            print("qudit", key, [(r["p"], f"{r['LER_unit_shift_exact']:.2e}") for r in qrows if r["code"] == key])
        ex.save_csv("qudit_level.csv", qrows)
        ex.save_csv("qudit_mc.csv", mrows)
        for r in mrows:
            print("mc", r["code"], r["device"], r["logical_error_rate"], r["exact_LER"], r["exact_within_CI"], round(r["seconds"], 2))
        key = cfg["qubit"]["code"]
        if status.get(key):
            t = time.perf_counter()
            rows = qubit_level(built[key], cfg["qubit"], lambda s: print(s, flush=True))
            ex.save_csv("qubit_level.csv", rows)
            out["qubit"] = {"code": key, "seconds": time.perf_counter() - t}
        else:
            out["qubit"] = "NOT RUN (gate-level steps 1-5 not all PASS)"
        ex.save_json("results.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="noise_layouts.toml")
    main(ap.parse_args().config)
