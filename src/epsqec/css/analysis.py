"""Exhaustive verification of the nested-ideal / Hermitian-dual structure of a CSS pair."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..ideals import (
    AdditiveCode,
    hermitian_dual,
    hermitian_dual_def6,
    orthogonal_exhaustive,
    trace_dual,
)
from ..ring import GaussianRing, zi


@dataclass
class CSSPair:
    ring: GaussianRing
    C1: AdditiveCode
    C2: AdditiveCode
    C2_dual: AdditiveCode  # true Hermitian orthogonal complement
    C2_dual_def6: AdditiveCode | None  # literal Definition 6 (principal case only)
    C1_dual: AdditiveCode

    @property
    def K(self) -> int:
        assert self.C2.size % self.C1.size == 0
        return self.C2.size // self.C1.size


def analyze_principal_pair(q: int, alpha1, alpha2, exhaustive_orth_limit: int = 5_000_000):
    """Return (CSSPair, report dict).  Every size is a popcount of an enumerated set."""
    R = GaussianRing(q)
    a1, a2 = R.reduce(alpha1), R.reduce(alpha2)
    C1 = AdditiveCode.principal(R, a1, "C1")
    C2 = AdditiveCode.principal(R, a2, "C2")
    D2 = hermitian_dual(C2)
    D2_def6 = hermitian_dual_def6(R, a2)
    D1 = hermitian_dual(C1)
    T2 = trace_dual(C2)
    DD2 = hermitian_dual(D2)

    t1, t2 = (int(a1[0]), int(a1[1])), (int(a2[0]), int(a2[1]))
    rep: dict = {"q": q, "alpha1": R.fmt(a1), "alpha2": R.fmt(a2), "|R|": R.size}
    # sizes: enumeration vs the two norm formulas
    rep["size_C1_enumerated"] = C1.size
    rep["size_C2_enumerated"] = C2.size
    rep["size_C1_paper_formula_q2_over_N"] = R.size / zi.norm(t1)
    rep["size_C2_paper_formula_q2_over_N"] = R.size / zi.norm(t2)
    rep["size_C1_gcd_formula"] = R.size // zi.ideal_index_in_Zq(t1, q)
    rep["size_C2_gcd_formula"] = R.size // zi.ideal_index_in_Zq(t2, q)
    rep["gcd(alpha1,q)"] = zi.gcd(t1, (q, 0))
    rep["gcd(alpha2,q)"] = zi.gcd(t2, (q, 0))
    rep["N(alpha1)_mod_q"] = int(R.norm(a1))
    rep["N(alpha2)_mod_q"] = int(R.norm(a2))
    # structure
    rep["C1_is_R_ideal"] = C1.is_R_module()
    rep["C2_is_R_ideal"] = C2.is_R_module()
    rep["C1_subset_C2"] = C1.issubset(C2)
    rep["index_C2_C1"] = C2.size // C1.size if C2.size % C1.size == 0 else None
    rep["K"] = rep["index_C2_C1"]
    # duals
    rep["size_C2_dual_true"] = D2.size
    rep["size_C2_dual_def6"] = D2_def6.size
    rep["size_C1_dual_true"] = D1.size
    rep["size_C2_trace_dual"] = T2.size
    rep["trace_dual_equals_hermitian_dual"] = T2 == D2
    rep["dual_true_equals_def6"] = D2 == D2_def6
    rep["C2_times_dual_true_eq_R"] = C2.size * D2.size == R.size
    rep["C2_times_dual_def6_eq_R"] = C2.size * D2_def6.size == R.size
    rep["double_dual_equals_C2"] = DD2 == C2
    rep["dual_true_subset_C1"] = D2.issubset(C1)
    rep["dual_def6_subset_C1"] = D2_def6.issubset(C1)
    rep["dual_true_is_R_ideal"] = D2.is_R_module()
    if C2.size * D2.size <= exhaustive_orth_limit:
        rep["dual_true_orthogonal_to_all_C2_exhaustive"] = orthogonal_exhaustive(C2, D2)
    if C2.size * D2_def6.size <= exhaustive_orth_limit:
        rep["dual_def6_orthogonal_to_all_C2_exhaustive"] = orthogonal_exhaustive(C2, D2_def6)
    # a generator of the true dual (it is principal: Z_q[i] is a principal ideal ring)
    gen = None
    for v in D2.vectors()[:, 0, :]:
        if AdditiveCode.principal(R, v) == D2:
            gen = R.fmt(v)
            break
    rep["dual_true_principal_generator_found"] = gen
    pair = CSSPair(R, C1, C2, D2, D2_def6, D1)
    return pair, rep


def analyze_z9_table_row() -> dict:
    """Tables 1-3 list R = Z_9, C1 = <3>, C2 = <1>.  Z_9 has no 'i'; sigma is the identity and
    the Hermitian product is the ordinary product.  Compute everything by enumeration."""
    q = 9
    R = np.arange(q)
    C1 = sorted({(3 * r) % q for r in R})
    C2 = sorted({(1 * r) % q for r in R})
    dual_C2 = [y for y in R if all((c * y) % q == 0 for c in C2)]
    def6 = sorted({(1 * r) % q for r in R})  # <sigma(1)> = <1>
    return {
        "C1": C1,
        "C2": C2,
        "size_C1": len(C1),
        "size_C2": len(C2),
        "index": len(C2) // len(C1),
        "size_C2_dual_true": len(dual_C2),
        "C2_dual_true": [int(y) for y in dual_C2],
        "size_C2_dual_def6": len(def6),
        "K_theorem4_formula": len(C2) // len(C1),
    }
