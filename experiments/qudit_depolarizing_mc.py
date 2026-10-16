"""Step 6 completion: Monte Carlo for qudit DEPOLARIZING noise (the spec asks for exact + MC for both
qudit models), checked against the exact formula, plus the unit-shift pattern counts that explain
the exact LER values (e.g. Z65: every unit-shift pattern is corrected -> LER = 0).

Every (code, p) gets an independent seed (SeedSequence.spawn).  The first run of this script
(qudit_depolarizing_mc-20261016T012657Z) used seed 77 for all codes; the hit count was then shared
(8155-8160 instead of 8000 at p = 0.2, z = 2.0) and the exact value fell just outside the 95% CI
for Z25 and Z65 at p = 0.2 -- one common fluctuation, not three.  Besides the unconditional CI we
also test failures | hits ~ Binomial(hits, 1 - r), r = (N_X N_Z - 1)/(d^2 - 1).

PASS criterion (added after the second run had been inspected; its smallest conditional p-value was
0.18, so the verdict does not depend on this choice): every row's conditional binomial p-value
> alpha / #rows (Bonferroni, alpha = 0.05); otherwise the run is marked FAIL. The unconditional 95% CI
column is reported but is not the criterion (with 6 rows one miss is expected ~26% of the time).

    .venv/Scripts/python.exe experiments/qudit_depolarizing_mc.py
"""
from __future__ import annotations

import numpy as np
import torch
from scipy.stats import binomtest

from epsqec.benchmarking import Experiment
from epsqec.css.build import build
from epsqec.noise.montecarlo import RingMC
from epsqec.simulation.awgn import clopper_pearson

SPECS = [{"key": "Z25"}, {"key": "Z65", "q": 65, "alpha1": [4, 7], "alpha2": [3, 2], "eps": "multiples"}, {"key": "Z85"}]


def main():
    cfg = {"codes": [s["key"] for s in SPECS], "p": [0.05, 0.2], "trials": 40000, "batch": 2000, "seed": 77,
           "seeding": "SeedSequence(seed).spawn(len(codes) * len(p)), one child per (code, p)",
           "pass_criterion": "all conditional_binom_p > alpha / n_rows (Bonferroni)", "alpha": 0.05}
    with Experiment("quantum", "qudit_depolarizing_mc", cfg, seed=cfg["seed"]) as ex:
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        rows, pats = [], []
        children = iter(np.random.SeedSequence(cfg["seed"]).spawn(len(SPECS) * len(cfg["p"])))
        for spec in SPECS:
            b = build(spec)
            mc = RingMC(b, dev)
            pc = mc.unit_shift_pattern_counts()
            NX, NZ = mc.correctable_counts()
            pats.append({"code": spec["key"], **pc, "N_X (all u in R)": NX, "N_Z (all v in R)": NZ, "|R|": b.space.dim})
            for p in cfg["p"]:
                child = next(children)
                seed = int(child.generate_state(1)[0])
                r = mc.run(p, cfg["trials"], cfg["batch"], seed=seed, model="depolarizing")
                k = r["trials"] - r["successes"]
                lo, hi = clopper_pearson(k, r["trials"])
                exact = 1 - mc.exact_depolarizing(p)
                d = b.space.dim
                r_ok = (NX * NZ - 1) / (d * d - 1)
                cond_p = binomtest(k, r["hits"], 1 - r_ok).pvalue if r["hits"] else 1.0
                rows.append({"code": spec["key"], "model": "depolarizing", "p": p, "seed": seed, "trials": r["trials"],
                             "hits": r["hits"], "failures": k, "MC_LER": k / r["trials"], "ci_low": lo, "ci_high": hi,
                             "exact_LER": exact, "exact_within_CI": lo <= exact <= hi,
                             "conditional_binom_p": float(cond_p), "device": r["device"], "seconds": r["seconds"]})
                print(rows[-1])
                if not rows[-1]["exact_within_CI"]:
                    ex.note(f"{spec['key']} p={p}: exact outside 95% CI")
            print(pats[-1])
        thr = cfg["alpha"] / len(rows)
        for x in rows:
            x["conditional_pass"] = bool(x["conditional_binom_p"] > thr)
        if not all(x["conditional_pass"] for x in rows):
            ex.fail(f"conditional binomial test below Bonferroni threshold {thr:.4g} in "
                    f"{sum(not x['conditional_pass'] for x in rows)} row(s)")
        ex.save_csv("depolarizing_mc.csv", rows)
        ex.save_csv("unit_shift_patterns.csv", pats)
        ex.save_json("results.json", {"rows": rows, "patterns": pats, "bonferroni_threshold": thr,
                                      "pass_criterion": cfg["pass_criterion"]})


if __name__ == "__main__":
    main()
