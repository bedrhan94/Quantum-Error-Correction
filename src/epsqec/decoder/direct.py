"""Direct quotient-map coset labelling (comparison baseline, NOT the paper's decoder).

For principal pairs with alpha2 | alpha1 | q in Z[i] (true for every example in the paper),
    C2 / C1  =  alpha2 Z[i] / alpha1 Z[i]  ~=  Z[i] / (pi),   pi = alpha1 / alpha2 = a + b i.
If gcd(a, b) = 1, Z[i]/(pi) ~= Z_N with N = N(pi) via  x + y i  ->  x + y s (mod N),
s = -a b^{-1} (mod N).  The coset of y in C2 is then one exact Z[i] division plus one modular
reduction - a cost independent of |eps|.  Used only to put the paper's O(|eps|)
membership-test decoder in context.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..ring import zi


@dataclass
class DirectCosetDecoder:
    q: int
    alpha1: tuple[int, int]
    alpha2: tuple[int, int]
    eps: np.ndarray  # (k, 1, 2) or (k, 2)

    def __post_init__(self):
        a1, a2, q = tuple(map(int, self.alpha1)), tuple(map(int, self.alpha2)), self.q
        if not (zi.divides(a2, a1) and zi.divides(a1, (q, 0))):
            raise ValueError("direct decoder needs alpha2 | alpha1 | q in Z[i]")
        num = zi.mul(a1, zi.conj(a2))
        n2 = zi.norm(a2)
        self.pi = (num[0] // n2, num[1] // n2)
        assert zi.mul(self.pi, a2) == a1
        a, b = self.pi
        if math.gcd(a, b) != 1:
            raise NotImplementedError("pi = alpha1/alpha2 is not primitive; Z[i]/(pi) not cyclic")
        self.N = zi.norm(self.pi)
        self.s = (-a * pow(b, -1, self.N)) % self.N
        self._a2, self._n2 = a2, n2
        eps = np.asarray(self.eps).reshape(-1, 2)
        self.table = np.full(self.N, -1, dtype=np.int64)
        for k, e in enumerate(eps):
            lab = self.label((int(e[0]), int(e[1])))
            if self.table[lab] >= 0:
                raise ValueError("eps is not a transversal (two reps share a label)")
            self.table[lab] = k
        if (self.table < 0).any():
            raise ValueError("eps does not meet every coset")
        self._eps = eps

    def label(self, y) -> int:
        y = (int(y[0]) % self.q, int(y[1]) % self.q)
        num = zi.mul(y, zi.conj(self._a2))
        if num[0] % self._n2 or num[1] % self._n2:
            raise KeyError("y not in C2")
        x, w = num[0] // self._n2, num[1] // self._n2  # z = y / alpha2 in Z[i]
        return (x + w * self.s) % self.N

    def decode(self, y):
        try:
            k = int(self.table[self.label(y)])
        except KeyError:
            return None, None
        e = self._eps[k]
        c = ((int(y[0]) - int(e[0])) % self.q, (int(y[1]) - int(e[1])) % self.q)
        return e, c
