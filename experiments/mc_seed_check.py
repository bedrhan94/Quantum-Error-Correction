"""Follow-up of noise_layouts: the Z25 Monte-Carlo estimate (40 000 trials, one seed shared by CPU and
GPU) fell just outside the 95% CI of the exact value.  Re-run with independent seeds to decide
between a statistical fluctuation and a bias of the trajectory simulator.

    .venv/Scripts/python.exe experiments/mc_seed_check.py
"""
from __future__ import annotations

import numpy as np
import torch

from epsqec.benchmarking import Experiment
from epsqec.css.build import build
from epsqec.noise.montecarlo import RingMC
from epsqec.simulation.awgn import clopper_pearson


def main():
    cfg = {"code": "Z25", "p": 0.05, "seeds": list(range(101, 111)), "trials_per_seed": 40000, "batch": 4000}
    with Experiment("quantum", "mc_seed_check", cfg, seed=101) as ex:
        b = build({"key": cfg["code"]})
        mc = RingMC(b, "cuda" if torch.cuda.is_available() else "cpu")
        exact = 1 - mc.exact_unit_shift(cfg["p"])
        rows, fails, n = [], 0, 0
        for s in cfg["seeds"]:
            r = mc.run(cfg["p"], cfg["trials_per_seed"], cfg["batch"], seed=s)
            k = r["trials"] - r["successes"]
            lo, hi = clopper_pearson(k, r["trials"])
            rows.append({"seed": s, "failures": k, "trials": r["trials"], "LER": k / r["trials"], "ci_low": lo, "ci_high": hi,
                         "exact_within_CI": lo <= exact <= hi, "device": r["device"]})
            fails += k
            n += r["trials"]
        lo, hi = clopper_pearson(fails, n)
        z = (fails - n * exact) / np.sqrt(n * exact * (1 - exact))
        summary = {"exact_LER": exact, "pooled_failures": fails, "pooled_trials": n, "pooled_LER": fails / n,
                   "pooled_ci": [lo, hi], "exact_within_pooled_CI": lo <= exact <= hi, "z_score": float(z),
                   "seeds_with_exact_outside_CI": sum(not r["exact_within_CI"] for r in rows)}
        ex.save_csv("seeds.csv", rows)
        ex.save_json("results.json", {"summary": summary, "rows": rows})
        if not summary["exact_within_pooled_CI"]:
            ex.fail("pooled estimate inconsistent with the exact value")
        print(summary)
        for r in rows:
            print(r)


if __name__ == "__main__":
    main()
