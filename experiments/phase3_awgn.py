"""Phase 3 - AWGN SER reconstruction of the paper's Figures 1-3 (independent reconstruction).

Reproducible command:
    .venv/Scripts/python.exe experiments/phase3_awgn.py [--config phase3_awgn.toml] [--figs fig1,fig2,fig3]
Writes results/awgn/<exp_id>/{ser_<fig>.csv, results.json} ; plots: experiments/plot_awgn.py
"""
from __future__ import annotations

import argparse

import numpy as np

from epsqec.benchmarking import Experiment, load_config
from epsqec.simulation import awgn as A
from epsqec.simulation import constellations as C


def build_detector(c: dict) -> tuple[A.Detector, dict]:
    if "const" in c:
        kind, m = c["const"].split(":")
        pts = C.square_qam(int(m)) if kind == "square" else C.cross_qam(int(m))
        return A.Detector("ml", pts), C.describe(pts)
    w = complex(*c["w"])
    res = C.gaussian_residues(w)
    if "g" in c:
        g = complex(*c["g"])
        sub = C.coded_subset(w, g)
        if c["kind"] == "ml":
            return A.Detector("ml", sub), C.describe(sub)
        det = A.Detector("coset", res, w=w, g=g, tx_points=sub, normalize_on=c.get("normalize_on", "tx"))
        return det, C.describe(sub)
    if c["kind"] == "ml":
        return A.Detector("ml", res), C.describe(res)
    return A.Detector("ring", res, w=w), C.describe(res)


def main(cfg_path: str, figs: list[str]):
    cfg = load_config(cfg_path)
    with Experiment("awgn", "phase3_awgn", cfg, seed=cfg["seed"]) as ex:
        out = {"category": "independent reconstruction", "figures": {}}
        for fig in figs:
            rows = []
            for i, c in enumerate(cfg[fig]["curves"]):
                det, desc = build_detector(c)
                r = A.simulate_ser(det, cfg[fig]["snr_db"], min_errors=cfg["min_errors"],
                                   max_symbols=cfg["max_symbols"], batch=cfg["batch"],
                                   seed=cfg["seed"] + 1000 * i, device=cfg["device"], ci=cfg["ci_level"])
                for row in r:
                    row.update({"curve": c["id"], "label": c["label"], "bits_per_symbol": desc["bits_per_symbol"],
                                "dmin2_over_Es": desc["dmin2_over_Es"],
                                "ebn0_db": row["snr_db"] - 10 * np.log10(desc["bits_per_symbol"]),
                                "Es_tx_normalised": det._cache.get("Es_tx", 1.0)})
                rows += r
                print(fig, c["id"], [(x["snr_db"], f"{x['ser']:.3g}", x["errors"]) for x in r])
                out["figures"].setdefault(fig, {})[c["id"]] = {"constellation": desc, "label": c["label"]}
            # closed-form references for square QAM
            for M in (16, 256, 1024):
                cid = f"qam{M}_ml"
                if any(c["id"] == cid for c in cfg[fig]["curves"]):
                    for s in cfg[fig]["snr_db"]:
                        rows.append({"curve": f"qam{M}_exact", "label": f"{M}-QAM exact formula",
                                     "snr_db": s, "ser": float(A.ser_square_qam_exact(M, s)), "detector": "closed-form"})
            ex.save_csv(f"ser_{fig}.csv", rows)
        ex.save_json("results.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="phase3_awgn.toml")
    ap.add_argument("--figs", default="fig1,fig2,fig3")
    a = ap.parse_args()
    main(a.config, a.figs.split(","))
