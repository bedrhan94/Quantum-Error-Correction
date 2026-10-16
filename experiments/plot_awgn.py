"""Plot Figures 1-3 reconstructions and side-by-side comparisons with the paper's raster figures.

    .venv/Scripts/python.exe experiments/plot_awgn.py [--exp <results/awgn/<id>>]
Default: the most recent results/awgn/phase3_awgn-* directory.  Writes figures/awgn_*.png and
results/awgn/<id>/crossings.json (SNR at which each curve reaches given SER targets, by
log-linear interpolation between simulated points; never extrapolated).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

from epsqec.benchmarking.plotting import SLOTS, TEXT2, footer, setup

ROOT = Path(__file__).resolve().parents[1]

STYLE = {
    # fig1
    "qam16_ml": (SLOTS["blue"], "s", "-"),
    "qam32_ml": (SLOTS["orange"], "^", "-"),
    "rq25_w5_ring": (SLOTS["aqua"], "o", "-"),
    "rq25_w5_ml": (SLOTS["aqua"], "o", "--"),
    "rq25_w34_ring": (SLOTS["violet"], "D", "-"),
    "rq25_w34_ml": (SLOTS["violet"], "D", "--"),
    # fig2
    "qam256_ml": (SLOTS["blue"], "s", "-"),
    "qam1024_ml": (SLOTS["orange"], "^", "-"),
    "rq625_w25_ring": (SLOTS["aqua"], "o", "-"),
    "rq625_w25_ml": (SLOTS["aqua"], "o", "--"),
    "rq625_w724_ring": (SLOTS["violet"], "D", "-"),
    # fig3
    "unc625_ring": (SLOTS["gray"], "s", "-"),
    "coded125_coset_tx": (SLOTS["blue"], "o", "-"),
    "coded125_coset_all": (SLOTS["blue"], "o", ":"),
    "coded125_ml": (SLOTS["aqua"], "v", "--"),
    "qam128_ml": (SLOTS["orange"], "^", "-"),
}
TITLES = {
    "fig1": "Fig. 1 reconstruction - uncoded SER, 25-element R_Q vs 16/32-QAM",
    "fig2": "Fig. 2 reconstruction - uncoded SER, 625-element R_Q vs 256/1024-QAM",
    "fig3": "Fig. 3 reconstruction - coded <2+i> (125) vs uncoded 625 + equal-rate baseline",
}


def load(exp: Path, fig: str):
    rows = list(csv.DictReader(open(exp / f"ser_{fig}.csv", encoding="utf-8")))
    curves = {}
    for r in rows:
        curves.setdefault(r["curve"], []).append(r)
    return curves


def crossing(xs, ys, target):
    """First SNR where SER <= target, log-linear interpolation; None if not reached."""
    for i in range(1, len(xs)):
        if ys[i - 1] > target >= ys[i] and ys[i] > 0:
            l0, l1 = np.log10(ys[i - 1]), np.log10(ys[i])
            return float(xs[i - 1] + (np.log10(target) - l0) / (l1 - l0) * (xs[i] - xs[i - 1]))
    return None


def draw(ax, curves, fig, xkey="snr_db"):
    for cid, rows in curves.items():
        if cid.endswith("_exact"):
            continue
        col, mk, ls = STYLE.get(cid, (SLOTS["red"], "x", "-"))
        x = np.array([float(r[xkey]) for r in rows])
        y = np.array([float(r["ser"]) for r in rows])
        e = np.array([int(r["errors"]) for r in rows])
        lo = np.array([float(r["ci_low"]) for r in rows])
        hi = np.array([float(r["ci_high"]) for r in rows])
        keep = e > 0  # zero-error points are not drawn (no SER estimate); see csv for upper bounds
        ax.errorbar(x[keep], y[keep], yerr=[y[keep] - lo[keep], hi[keep] - y[keep]], color=col, marker=mk,
                    ls=ls, label=rows[0]["label"], capsize=2, elinewidth=0.8, markerfacecolor=col,
                    markeredgecolor="white", markeredgewidth=0.8)
    for cid, rows in curves.items():
        if cid.endswith("_exact") and xkey == "snr_db":
            x = [float(r["snr_db"]) for r in rows]
            y = [float(r["ser"]) for r in rows]
            ax.plot(x, y, color=TEXT2, lw=0.9, ls=(0, (1, 2)), label=rows[0]["label"] if fig != "fig2" else None)
    ax.set_yscale("log")
    ax.set_ylim(1e-6 if fig != "fig1" else 1e-5, 1.2)
    ax.set_ylabel("Symbol error rate (SER)")
    ax.set_xlabel("SNR  $E_s/N_0$  (dB)" if xkey == "snr_db" else "$E_b/N_0$  (dB)")


def main(exp: Path):
    setup()
    status = json.load(open(exp / "status.json"))
    cfg = json.load(open(exp / "config.json"))
    env = json.load(open(exp / "env.json"))
    dev = "cuda" if env.get("torch_cuda_available") else "cpu"
    tag = (f"exp {status['experiment_id']} | config hash {env['config_hash']} | independent reconstruction | "
           f"min_errors={cfg['min_errors']}, max_symbols={cfg['max_symbols']:.0e}, seed={cfg['seed']}, device={dev}")
    figdir = ROOT / "figures"
    cross = {}
    for fig in ("fig1", "fig2", "fig3"):
        curves = load(exp, fig)
        # --- our figure alone
        f, ax = plt.subplots(figsize=(8.2, 5.6))
        draw(ax, curves, fig)
        ax.set_title(TITLES[fig], fontsize=11)
        ax.legend(fontsize=8, loc="lower left")
        footer(f, tag)
        f.tight_layout(rect=(0, 0.03, 1, 1))
        f.savefig(figdir / f"awgn_{fig}_reconstruction.png")
        plt.close(f)
        # --- side by side with the paper's raster figure
        f, axs = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw={"width_ratios": [1, 1.05]})
        img = mpimg.imread(ROOT / "figures" / "paper_extracted" / f"paper_{fig}.jpg")
        axs[0].imshow(img)
        axs[0].axis("off")
        axs[0].set_title(f"Paper, {fig.replace('fig', 'Fig. ')} (raster extracted from PDF p.{20 if fig != 'fig3' else 21})",
                         fontsize=10)
        draw(axs[1], curves, fig)
        axs[1].set_xlim(*{"fig1": (-1, 21), "fig2": (9, 35), "fig3": (-1, 35)}[fig])
        axs[1].set_title("This work (same axes; error bars = 95% Clopper-Pearson)", fontsize=10)
        axs[1].legend(fontsize=7.5, loc="lower left")
        footer(f, tag)
        f.tight_layout(rect=(0, 0.03, 1, 1))
        f.savefig(figdir / f"awgn_{fig}_side_by_side.png")
        plt.close(f)
        # --- crossings
        for cid, rows in curves.items():
            if cid.endswith("_exact"):
                continue
            xs = [float(r["snr_db"]) for r in rows]
            ys = [float(r["ser"]) for r in rows]
            bps = float(rows[0]["bits_per_symbol"])
            cross.setdefault(fig, {})[cid] = {
                "bits_per_symbol": bps,
                **{f"EsN0_at_SER_{t:g}": crossing(xs, ys, t) for t in (1e-1, 1e-2, 1e-3, 1e-4)},
            }
            for t in (1e-2, 1e-3, 1e-4):
                v = cross[fig][cid][f"EsN0_at_SER_{t:g}"]
                cross[fig][cid][f"EbN0_at_SER_{t:g}"] = None if v is None else v - 10 * np.log10(bps)
    # --- Fig. 3 on an Eb/N0 axis (rate-fair view)
    curves = load(exp, "fig3")
    f, ax = plt.subplots(figsize=(8.2, 5.6))
    draw(ax, curves, "fig3", xkey="ebn0_db")
    ax.set_title("Fig. 3 data on an $E_b/N_0$ axis (625 pts: 9.29 b/sym; 125 pts: 6.97; 128-QAM: 7)", fontsize=10.5)
    ax.legend(fontsize=8, loc="lower left")
    footer(f, tag)
    f.tight_layout(rect=(0, 0.03, 1, 1))
    f.savefig(figdir / "awgn_fig3_ebn0.png")
    plt.close(f)
    json.dump(cross, open(exp / "crossings.json", "w"), indent=2)
    print(json.dumps(cross["fig3"], indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default=None)
    a = ap.parse_args()
    exp = Path(a.exp) if a.exp else sorted((ROOT / "results" / "awgn").glob("phase3_awgn-*"))[-1]
    main(exp)
