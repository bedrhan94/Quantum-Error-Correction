"""epsilon-decoder (Definition 10, Example 5/8, Appendix A.1) with instrumented membership tests.

The paper states a cost of O(|eps|) "membership tests".  To avoid hiding the cost of a single
membership test, three interchangeable oracles are provided and timed separately:

  "bitmap"    : precomputed boolean table over R^n.  Pre-processing O(q^(2n)) time and memory;
                each test = index computation O(n) + one table lookup.
  "pyset"     : Python set of tuples, as in the authors' code (C1.elements).  Pre-processing
                O(|R|) ring multiplications to enumerate C1, memory O(|C1| n); each test hashes
                an n-vector.
  "algebraic" : n = 1, C1 = <alpha1>.  x in <alpha1>  <=>  g | x in Z[i] with g = gcd(alpha1, q)
                (since <alpha1> = <g> in Z_q[i] and g | q).  No enumeration; each test is two
                big-int products and two reductions mod N(g).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from ..ideals import AdditiveCode
from ..ring import zi


@dataclass
class DecodeResult:
    status: str  # ok | not_in_C2 | no_candidate | non_unique
    e: np.ndarray | None
    c: np.ndarray | None
    n_membership_tests: int
    n_candidates: int


def membership_oracle(kind: str, code: AdditiveCode, generator=None):
    """Return (test(x)->bool, info dict with preprocessing time / memory estimate)."""
    ring, n = code.ring, code.n
    t0 = time.perf_counter()
    if kind == "bitmap":
        mask = code.mask
        w = np.array([ring.size ** j for j in range(n)], dtype=np.int64)
        q = ring.q

        def test(x):
            x = np.asarray(x).reshape(n, 2)
            return bool(mask[int(((x[:, 0] % q) * q + (x[:, 1] % q)) @ w)])

        mem = mask.nbytes
    elif kind == "pyset":
        q = ring.q
        s = {tuple(map(int, v.reshape(-1))) for v in code.vectors()}

        def test(x):
            return tuple(int(t) % q for t in np.asarray(x).reshape(-1)) in s

        mem = len(s) * (n * 2 * 28 + 56)  # rough CPython estimate, reported as an estimate
    elif kind == "algebraic":
        if n != 1 or generator is None:
            raise ValueError("algebraic oracle implemented for principal ideals (n = 1) only")
        g = zi.gcd((int(generator[0]), int(generator[1])), (ring.q, 0))
        Ng = zi.norm(g)
        ga, gb = g

        def test(x):
            a, b = (int(t) for t in np.asarray(x).reshape(-1))
            # x * conj(g) = (a ga + b gb) + (b ga - a gb) i
            return (a * ga + b * gb) % Ng == 0 and (b * ga - a * gb) % Ng == 0

        mem = 0
    else:
        raise ValueError(kind)
    return test, {"kind": kind, "preprocess_s": time.perf_counter() - t0, "memory_bytes_est": mem}


@dataclass
class EpsilonDecoder:
    C2: AdditiveCode
    C1: AdditiveCode
    eps: np.ndarray  # (k, n, 2)
    oracle: str = "bitmap"
    alpha1: object = None
    alpha2: object = None
    check_in_C2: bool = True  # Appendix A.1 tests y in C2 first; the authors' file does not
    early_stop: bool = False  # Appendix A.1 scans all of eps (needed to *verify* uniqueness)
    info: dict = field(default_factory=dict)

    def __post_init__(self):
        ring = self.C2.ring
        self.eps = ring.reduce(np.asarray(self.eps))
        if self.eps.ndim == 2:
            self.eps = self.eps[:, None, :]
        self._in_C1, i1 = membership_oracle(self.oracle, self.C1, self.alpha1)
        self._in_C2, i2 = membership_oracle(self.oracle, self.C2, self.alpha2)
        self.info = {"C1_oracle": i1, "C2_oracle": i2}

    def decode(self, y) -> DecodeResult:
        ring = self.C2.ring
        y = ring.reduce(np.asarray(y)).reshape(self.C2.n, 2)
        tests = 0
        if self.check_in_C2:
            tests += 1
            if not self._in_C2(y):
                return DecodeResult("not_in_C2", None, None, tests, 0)
        cands = []
        for e in self.eps:
            tests += 1
            if self._in_C1(ring.sub(y, e)):
                cands.append(e)
                if self.early_stop:
                    break
        if not cands:
            return DecodeResult("no_candidate", None, None, tests, 0)
        if len(cands) > 1:
            return DecodeResult("non_unique", None, None, tests, len(cands))
        e = cands[0]
        return DecodeResult("ok", e, ring.sub(y, e), tests, 1)

    # vectorised exhaustive check: candidate matrix for many y at once (bitmap only)
    def candidate_matrix(self, Y) -> np.ndarray:
        ring = self.C2.ring
        Y = ring.reduce(np.asarray(Y))
        diff = ring.sub(Y[:, None], self.eps[None])  # (m, k, n, 2)
        return self.C1.mask[ring.vec_index(diff)]
