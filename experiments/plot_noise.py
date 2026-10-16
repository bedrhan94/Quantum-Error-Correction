"""Plot Phase 6 qubit-level results: logical error rate vs physical error probability,
one panel per channel (small multiples), four codes at equal logical capacity K = 5.

    .venv/Scripts/python.exe experiments/plot_noise.py [--exp results/quantum/phase6_noise-...]
Uses the most recent phase6 run that contains qubit_level.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from epsqec.benchmarking.plotting import SLOTS, TEXT2, footer, setup

ROOT = Path(__file__).resolve().parents[1]
STY = {
    "ring": (SLOTS["blue"], "o", "-", "ring Z_25[i] code (10 qubits)"),
    "modular": (SLOTS["orange"], "s", "-", "standard qudit CSS Z_625 (10 qubits)"),
    "no QEC": (SLOTS["gray"], "^", "--", "no QEC (3 qubits)"),
    "[[5,1,3]]": (SLOTS["aqua"], "D", "-", "[[5,1,3]] x 3 (15 qubits)"),
}
TITLE = {"bit_flip": "bit flip", "phase_flip": "phase flip", "depolarizing": "depolarizing",
         "amplitude_damping": "amplitude damping (gamma)", "phase_damping": "phase damping (lambda)"}


def main(exp: Path):
    setup()
    rows = list(csv.DictReader(open(exp / "qubit_level.csv", encoding="utf-8")))
    env = json.load(open(exp / "env.json"))
    st = json.load(open(exp / "status.json"))
    chans = list(dict.fromkeys(r["channel"] for r in rows))
    f, axs = plt.subplots(1, len(chans), figsize=(4.0 * len(chans), 5.0), sharey=True)
    for ax, ch in zip(axs, chans):
        for key, (col, mk, ls, lab) in STY.items():
            rr = [r for r in rows if r["channel"] == ch and r["code"].startswith(key)]
            if not rr:
                continue
            x = np.array([float(r["p"]) for r in rr])
            y = np.array([max(float(r["logical_error_rate"]), 1e-12) for r in rr])
            ax.loglog(x, y, color=col, marker=mk, ls=ls, label=lab, markeredgecolor="white", markeredgewidth=0.7)
        ax.loglog([1e-4, 0.3], [1e-4, 0.3], color=TEXT2, lw=0.8, ls=(0, (1, 2)), label="y = p")
        ax.set_title(TITLE.get(ch, ch), fontsize=10)
        ax.set_xlabel("physical error probability per qubit")
        ax.set_ylim(1e-9, 1.2)
    axs[0].set_ylabel("logical error rate  (1 - entanglement fidelity, K = 5)")
    h, l = axs[0].get_legend_handles_labels()
    f.legend(h, l, loc="lower center", ncol=5, fontsize=8.5, bbox_to_anchor=(0.5, 0.035))
    f.suptitle("Phase 6 - code-capacity noise on the qubit embedding, equal logical capacity K = 5", fontsize=11)
    footer(f, f"exp {st['experiment_id']} | config hash {env['config_hash']} | exact density-matrix simulation "
              f"(CPU complex128); ideal syndrome extraction and recovery")
    f.tight_layout(rect=(0, 0.11, 1, 0.95))
    out = ROOT / "figures" / "noise_qubit_level_LER.png"
    f.savefig(out)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default=None)
    a = ap.parse_args()
    if a.exp:
        exp = Path(a.exp)
    else:
        cands = [d for d in sorted((ROOT / "results" / "quantum").glob("phase6_noise-*")) if (d / "qubit_level.csv").exists()]
        exp = cands[-1]
    main(exp)
