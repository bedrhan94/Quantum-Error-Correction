"""Build every object needed by the quantum phases from a small spec dict (enumeration only)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..decoder import greedy_transversal, multiples_transversal
from ..ideals import AdditiveCode, hermitian_dual, hermitian_dual_def6
from ..ring import GaussianRing
from ..stabilizer import QuditSpace, RingCSSCode
from .examples import PAPER_EXAMPLES


@dataclass
class Built:
    key: str
    ring: GaussianRing
    space: QuditSpace
    C1: AdditiveCode
    C2: AdditiveCode
    D_true: AdditiveCode
    D_def6: AdditiveCode | None
    eps: np.ndarray  # (K, n, 2)
    code: RingCSSCode  # with the true Hermitian dual
    code_def6: RingCSSCode | None

    @property
    def C1_dual(self) -> AdditiveCode:
        return hermitian_dual(self.C1)


def build(spec: dict) -> Built:
    key = spec["key"]
    if key in PAPER_EXAMPLES and "q" not in spec:
        pe = PAPER_EXAMPLES[key]
        spec = {**spec, "q": pe.q, "alpha1": pe.alpha1, "alpha2": pe.alpha2,
                "eps": spec.get("eps", "paper" if pe.eps_sets else "multiples")}
    q = spec["q"]
    R = GaussianRing(q, trace_convention=spec.get("trace_convention", "paper"))
    if "alpha1" in spec:  # principal, n = 1
        n = 1
        C1 = AdditiveCode.principal(R, spec["alpha1"], "C1")
        C2 = AdditiveCode.principal(R, spec["alpha2"], "C2")
        D6 = hermitian_dual_def6(R, spec["alpha2"])
    else:
        gens1 = np.array(spec["C1_generators"])
        gens2 = np.array(spec["C2_generators"])
        n = gens1.shape[1]
        C1 = AdditiveCode.submodule(R, gens1, "C1")
        C2 = AdditiveCode.submodule(R, gens2, "C2")
        D6 = None
    D = hermitian_dual(C2)
    space = QuditSpace(R, n)
    K = C2.size // C1.size
    mode = spec.get("eps", "greedy")
    if mode == "paper":
        pe = PAPER_EXAMPLES[key]
        name = "paper_example7" if "paper_example7" in pe.eps_sets else next(iter(pe.eps_sets))
        eps = R.reduce(np.array(pe.eps_sets[name]))[:, None, :]
    elif mode == "multiples":
        eps = multiples_transversal(R, spec["alpha2"], K)
    else:
        eps = greedy_transversal(C2, C1)
    code = RingCSSCode(space, C1, C2, D, f"{key}:true-dual")
    code6 = RingCSSCode(space, C1, C2, D6, f"{key}:def6-dual") if D6 is not None else None
    return Built(key, R, space, C1, C2, D, D6, eps, code, code6)
