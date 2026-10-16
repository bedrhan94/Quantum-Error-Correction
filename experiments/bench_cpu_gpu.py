"""CPU vs GPU benchmark of the verified simulators (run on an otherwise idle machine).

    .venv/Scripts/python.exe experiments/bench_cpu_gpu.py [--repeats 3]

Workloads (fixed, so runs are comparable over time):
  awgn_ml_1024qam   : 4e6 symbols, ML detection over 1024 points, Es/N0 = 30 dB
  awgn_ring_625     : 2e7 symbols, ring receiver (round + mod 25), Es/N0 = 30 dB
  awgn_coset_125    : 2e7 symbols, Section 4.2 coset decoder, Es/N0 = 30 dB
  dm_ring_ad        : exact density matrix, ring Z_25[i] code, amplitude damping p = 0.05
  mc_ring_z325      : 6000 Monte-Carlo trajectories on Z_325[i] (dim 105625), p = 0.05
GPU runs use complex64, CPU runs complex128 for the density matrix (complex64 elsewhere).
If CUDA is unavailable the GPU rows are recorded as NOT RUN (never substituted by CPU).
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import torch

from epsqec.benchmarking import Experiment
from epsqec.css.build import build
from epsqec.noise import logical_channel_metrics, ring_code_embedded
from epsqec.noise.montecarlo import RingMC
from epsqec.simulation import awgn as A
from epsqec.simulation import constellations as C


def awgn_job(kind, device, n):
    if kind == "awgn_ml_1024qam":
        det = A.Detector("ml", C.square_qam(1024))
    elif kind == "awgn_ring_625":
        det = A.Detector("ring", C.gaussian_residues(25), w=25)
    else:
        det = A.Detector("coset", C.gaussian_residues(25), w=25, g=2 + 1j, tx_points=C.coded_subset(25, 2 + 1j))
    r = A.simulate_ser(det, [30.0], min_errors=10**12, max_symbols=n, batch=2_000_000, seed=1, device=device)[0]
    return {"seconds": r["seconds"], "throughput_Msym_s": n / r["seconds"] / 1e6, "ser": r["ser"]}


def main(repeats):
    cfg = {"repeats": repeats, "seed": 1}
    with Experiment("benchmarks", "bench_cpu_gpu", cfg, seed=1) as ex:
        rows = []
        devices = ["cpu", "cuda"]
        b25 = build({"key": "Z25"})
        b325 = build({"key": "Z325"})
        ring = ring_code_embedded(b25)
        jobs = {
            "awgn_ml_1024qam": lambda dev: awgn_job("awgn_ml_1024qam", dev, 4_000_000),
            "awgn_ring_625": lambda dev: awgn_job("awgn_ring_625", dev, 20_000_000),
            "awgn_coset_125": lambda dev: awgn_job("awgn_coset_125", dev, 20_000_000),
            "dm_ring_ad": lambda dev: logical_channel_metrics(
                ring, "amplitude_damping", 0.05, device=dev,
                dtype=torch.complex128 if dev == "cpu" else torch.complex64),
            "mc_ring_z325": lambda dev: RingMC(b325, dev).run(0.05, 6000, 500, seed=1),
        }
        for name, job in jobs.items():
            for dev in devices:
                if dev == "cuda" and not torch.cuda.is_available():
                    rows.append({"workload": name, "device": dev, "status": "NOT RUN", "reason": "CUDA unavailable"})
                    continue
                times, last = [], None
                for _ in range(repeats):
                    if dev == "cuda":
                        torch.cuda.synchronize()
                        torch.cuda.reset_peak_memory_stats()
                    t = time.perf_counter()
                    last = job(dev)
                    if dev == "cuda":
                        torch.cuda.synchronize()
                    times.append(time.perf_counter() - t)
                row = {"workload": name, "device": dev, "status": "RUN", "repeats": repeats,
                       "wall_s_min": min(times), "wall_s_median": float(np.median(times))}
                if dev == "cuda":
                    row["gpu_peak_MB"] = torch.cuda.max_memory_allocated() / 2**20
                for k in ("throughput_Msym_s", "ser", "logical_error_rate"):
                    if isinstance(last, dict) and k in last:
                        row[k] = last[k]
                rows.append(row)
                print(row)
        # speedups
        for name in jobs:
            c = [r for r in rows if r["workload"] == name and r["device"] == "cpu" and r["status"] == "RUN"]
            g = [r for r in rows if r["workload"] == name and r["device"] == "cuda" and r["status"] == "RUN"]
            if c and g:
                g[0]["speedup_vs_cpu_median"] = c[0]["wall_s_median"] / g[0]["wall_s_median"]
        ex.save_csv("bench.csv", rows)
        ex.save_json("results.json", {"rows": rows})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    main(ap.parse_args().repeats)
