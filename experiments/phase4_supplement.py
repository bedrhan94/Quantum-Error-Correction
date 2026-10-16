"""Phase 4 supplement - is the hypothesis C2^perpH <= C1 of Theorem 4 needed?

Takes a nested pair C1 <= C2 in Z_25[i] that does NOT satisfy C2^perpH <= C1 and checks whether
S = <X(C1), Z(C2^perpH)> is still a commuting stabilizer group with a code space of dimension
|C2|/|C1|.  Reproducible command:
    .venv/Scripts/python.exe experiments/phase4_supplement.py
"""
from __future__ import annotations

import numpy as np

from epsqec.benchmarking import Experiment
from epsqec.decoder import greedy_transversal
from epsqec.ideals import AdditiveCode, hermitian_dual
from epsqec.ring import GaussianRing
from epsqec.stabilizer import QuditSpace, RingCSSCode


def main():
    cfg = {"q": 25, "alpha1": [10, 20], "alpha2": [2, 1], "seed": 0,
           "note": "alpha1 = 5(2-i) = 10-5i = 10+20i (mod 25); (2+i) | alpha1 but C2^perpH = <5(2+i)> is not inside <alpha1>"}
    with Experiment("quantum", "phase4_supplement", cfg, seed=0) as ex:
        R = GaussianRing(cfg["q"])
        C1 = AdditiveCode.principal(R, cfg["alpha1"])
        C2 = AdditiveCode.principal(R, cfg["alpha2"])
        D = hermitian_dual(C2)
        sp = QuditSpace(R, 1)
        code = RingCSSCode(sp, C1, C2, D, "no-dual-containment")
        eps = greedy_transversal(C2, C1)
        V = code.logical_states(eps)
        out = {
            "|C1|": C1.size, "|C2|": C2.size, "|C2^perpH|": D.size,
            "C1_subset_C2": C1.issubset(C2), "C2perp_subset_C1": D.issubset(C1),
            "commutation": code.commutation_exhaustive(),
            "dim_trace_formula": code.dim_trace_formula(), "dim_structural": code.dim_structural(),
            "dim_dense_nullspace": code.dim_nullspace_dense(), "K_|C2|/|C1|": C2.size // C1.size,
            "logical_gram_minus_I": float(np.abs(V.conj() @ V.T - np.eye(len(V))).max()),
        }
        ex.save_json("results.json", out)
        print(out)


if __name__ == "__main__":
    main()
