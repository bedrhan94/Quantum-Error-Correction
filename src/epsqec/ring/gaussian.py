"""The finite ring R_Q = Z_q[i] = {a + b i : a, b in Z_q},  i^2 = -1   (paper, Definition 3).

Representation
--------------
* an element is an int64 pair (a, b) with 0 <= a, b < q, stored in the last axis of an array;
* a vector x in R^n is an array of shape (n, 2);
* every element / vector also has an integer *index* used for bitmaps over R^n:
      idx(a + b i)            = a * q + b                         in [0, q^2)
      idx(x_0, ..., x_{n-1})  = sum_j idx(x_j) * (q^2)^j           in [0, q^(2n))
  All arithmetic is vectorised over leading axes so that exhaustive checks over the whole
  ring (or R^n) are a few numpy calls instead of Python loops.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def factorize(n: int) -> dict[int, int]:
    out: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


TRACE_CONVENTIONS = {
    # paper, Remark 3 (p.11):  Tr(a + bi) = (a + b) mod q   -- used for every result unless stated
    "paper": "Tr(a+bi) = (a + b) mod q   [makale, Remark 3]",
    # field-style trace t + sigma(t):  Tr(a + bi) = 2a mod q   (chi = omega^(2 Re t))
    "2re": "Tr(a+bi) = 2a mod q        [alternatif: chi = omega^(2 Re)]",
}


@dataclass(frozen=True)
class GaussianRing:
    """Z_q[i].  The additive character chi(t) = exp(2 pi i Tr(t) / q) (paper, Section 3 / Def. 8)
    is fixed HERE, in one place: every Z(v) phase, trace dual, syndrome value and circuit phase in
    the project calls ``trace``/``chi`` of the ring object, so switching ``trace_convention``
    switches the whole pipeline consistently."""

    q: int
    require_split_primes: bool = True
    trace_convention: str = "paper"

    def __post_init__(self):
        if self.q < 2:
            raise ValueError("q must be >= 2")
        if self.require_split_primes:
            bad = [p for p in factorize(self.q) if p % 4 != 1]
            if bad:
                raise ValueError(f"q={self.q} has prime divisors {bad} not = 1 (mod 4)")
        if self.trace_convention not in TRACE_CONVENTIONS:
            raise ValueError(f"unknown trace convention {self.trace_convention!r}")
        if self.trace_convention == "2re" and self.q % 2 == 0:
            raise ValueError("Tr = 2a is degenerate for even q")

    # ------------------------------------------------------------------ basics
    @property
    def size(self) -> int:
        return self.q * self.q

    def elem(self, a: int, b: int) -> np.ndarray:
        return np.array([a % self.q, b % self.q], dtype=np.int64)

    def elements(self) -> np.ndarray:
        """All q^2 elements, shape (q^2, 2), ordered by index."""
        a, b = np.divmod(np.arange(self.size, dtype=np.int64), self.q)
        return np.stack([a, b], axis=-1)

    def reduce(self, x) -> np.ndarray:
        return np.mod(np.asarray(x, dtype=np.int64), self.q)

    # ---------------------------------------------------------- ring operations
    def add(self, x, y):
        return np.mod(np.asarray(x) + np.asarray(y), self.q)

    def sub(self, x, y):
        return np.mod(np.asarray(x) - np.asarray(y), self.q)

    def neg(self, x):
        return np.mod(-np.asarray(x), self.q)

    def mul(self, x, y):
        x = np.asarray(x, dtype=np.int64)
        y = np.asarray(y, dtype=np.int64)
        a, b = x[..., 0], x[..., 1]
        c, d = y[..., 0], y[..., 1]
        return np.stack([np.mod(a * c - b * d, self.q), np.mod(a * d + b * c, self.q)], axis=-1)

    def scal(self, k, x):
        """Z_q-scalar multiple k * x (k an integer or integer array broadcastable to x[...,0])."""
        return np.mod(np.asarray(k, dtype=np.int64)[..., None] * np.asarray(x, dtype=np.int64), self.q)

    def conj(self, x):
        """Hermitian conjugation sigma(a + b i) = a - b i (Definitions 5-6)."""
        x = np.asarray(x, dtype=np.int64)
        return np.stack([x[..., 0], np.mod(-x[..., 1], self.q)], axis=-1)

    def norm(self, x):
        """N(x) = x * sigma(x) = a^2 + b^2  (mod q), an element of Z_q."""
        x = np.asarray(x, dtype=np.int64)
        return np.mod(x[..., 0] ** 2 + x[..., 1] ** 2, self.q)

    def trace(self, x):
        """Z_q-linear non-degenerate trace; default Tr(a + b i) = (a + b) mod q (paper, Remark 3)."""
        x = np.asarray(x, dtype=np.int64)
        if self.trace_convention == "2re":
            return np.mod(2 * x[..., 0], self.q)
        return np.mod(x[..., 0] + x[..., 1], self.q)

    def chi(self, x):
        """Additive character chi(t) = exp(2 pi i Tr(t) / q)."""
        return np.exp(2j * np.pi * self.trace(x) / self.q)

    def is_zero(self, x):
        x = np.asarray(x)
        return np.all(x == 0, axis=-1)

    def is_unit(self, x):
        """x is a unit iff N(x) is a unit of Z_q (q odd) -- cross-checked by brute force in tests."""
        n = self.norm(x)
        return np.vectorize(lambda t: math.gcd(int(t), self.q) == 1)(n)

    # ------------------------------------------------------ vectors in R^n
    def hermitian(self, x, y):
        """<x, y>_H = sum_j x_j sigma(y_j)   (Definition 5); x, y shape (..., n, 2)."""
        prod = self.mul(x, self.conj(y))
        return np.mod(prod.sum(axis=-2), self.q)

    # ------------------------------------------------------------ indexing
    def index(self, x) -> np.ndarray:
        """Index of element(s) (shape (...,2)) or vector(s) (shape (...,n,2))."""
        x = np.asarray(x, dtype=np.int64)
        e = x[..., 0] * self.q + x[..., 1]
        if e.ndim == 0:
            return e
        return e

    def vec_index(self, x) -> np.ndarray:
        """Index of vectors of shape (..., n, 2) in [0, q^(2n))."""
        e = self.index(x)  # (..., n)
        n = e.shape[-1]
        w = np.array([self.size ** j for j in range(n)], dtype=np.int64)
        return (e * w).sum(axis=-1)

    def from_index(self, idx) -> np.ndarray:
        idx = np.asarray(idx, dtype=np.int64)
        a, b = np.divmod(idx, self.q)
        return np.stack([a, b], axis=-1)

    def vec_from_index(self, idx, n: int) -> np.ndarray:
        idx = np.asarray(idx, dtype=np.int64)
        comps = []
        for _ in range(n):
            idx, r = np.divmod(idx, self.size)
            comps.append(self.from_index(r))
        return np.stack(comps, axis=-2)

    def all_vectors(self, n: int) -> np.ndarray:
        """All q^(2n) vectors of R^n, shape (q^(2n), n, 2) ordered by vec_index."""
        return self.vec_from_index(np.arange(self.size ** n, dtype=np.int64), n)

    def fmt(self, x) -> str:
        x = np.asarray(x)
        if x.ndim == 1:
            a, b = int(x[0]), int(x[1])
            return f"{a}+{b}i"
        return "(" + ", ".join(self.fmt(c) for c in x) + ")"
