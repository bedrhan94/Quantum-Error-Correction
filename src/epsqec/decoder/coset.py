"""Coset decomposition C2 = disjoint union_{e in eps} (C1 + e)   (Theorems 2-3, eq. (7)).

``check_transversal`` verifies a proposed eps by brute force:
  * eps subset of C2,
  * |eps| = [C2 : C1] (computed from enumerated sizes),
  * pairwise e_i - e_j not in C1 (disjointness),
  * the translates C1 + e are pairwise disjoint *as sets* and their union is exactly C2
    (coverage, checked element by element rather than by counting).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from ..ideals import AdditiveCode


def greedy_transversal(C2: AdditiveCode, C1: AdditiveCode) -> np.ndarray:
    """Theorem 2 procedure: e_1 = 0, then repeatedly pick the first element of C2 (index order)
    not covered by the union of the translates chosen so far."""
    ring, n = C2.ring, C2.n
    covered = np.zeros_like(C2.mask)
    c1 = C1.vectors()
    reps = []
    for idx in C2.indices:  # index 0 (the zero vector) comes first
        if covered[idx]:
            continue
        e = ring.vec_from_index(idx, n)
        reps.append(e)
        covered[ring.vec_index(ring.add(c1, e[None]))] = True
    return np.array(reps)


def multiples_transversal(ring, alpha2, k: int) -> np.ndarray:
    """eps = {0, alpha2, 2 alpha2, ..., (k-1) alpha2}  (the 'canonical transversal' of Ex. 6/7)."""
    alpha2 = ring.reduce(alpha2).reshape(2)
    out = ring.scal(np.arange(k), alpha2[None])  # (k, 2)
    return out[:, None, :]  # (k, n=1, 2)


@dataclass
class TransversalReport:
    size_C1: int
    size_C2: int
    index: int
    size_eps: int
    eps_in_C2: bool
    size_matches_index: bool
    pairwise_distinct_cosets: bool
    translates_disjoint: bool
    union_equals_C2: bool
    n_pair_checks: int
    bad_pairs: list

    @property
    def valid(self) -> bool:
        return (
            self.eps_in_C2
            and self.size_matches_index
            and self.pairwise_distinct_cosets
            and self.translates_disjoint
            and self.union_equals_C2
        )

    def as_dict(self):
        d = asdict(self)
        d["valid"] = self.valid
        return d


def check_transversal(eps, C2: AdditiveCode, C1: AdditiveCode) -> TransversalReport:
    ring = C2.ring
    eps = ring.reduce(np.asarray(eps))
    if eps.ndim == 2:
        eps = eps[:, None, :]
    s1, s2 = C1.size, C2.size
    index = s2 // s1 if s2 % s1 == 0 else -1
    in_c2 = bool(C2.contains(eps).all())
    bad = []
    pairs = 0
    for i in range(len(eps)):
        for j in range(i + 1, len(eps)):
            pairs += 1
            if C1.contains(ring.sub(eps[i], eps[j])):
                bad.append((i, j))
    c1 = C1.vectors()
    count = np.zeros(ring.size ** C2.n, dtype=np.int64)
    for e in eps:
        np.add.at(count, ring.vec_index(ring.add(c1, e[None])), 1)
    disjoint = bool((count <= 1).all())
    union_eq = bool(np.array_equal(count > 0, C2.mask))
    return TransversalReport(
        size_C1=s1,
        size_C2=s2,
        index=index,
        size_eps=len(eps),
        eps_in_C2=in_c2,
        size_matches_index=(len(eps) == index),
        pairwise_distinct_cosets=(not bad),
        translates_disjoint=disjoint,
        union_equals_C2=union_eq,
        n_pair_checks=pairs,
        bad_pairs=bad,
    )
